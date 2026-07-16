from __future__ import annotations

import html
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .config import Settings
from .ledger import Ledger
from .ollama_client import OllamaClient, OllamaError
from .task_queue import TaskQueue


settings = Settings.from_env(os.getenv("MATVERSE_WORKSPACE", Path.cwd()))
queue = TaskQueue(settings, workers=int(os.getenv("MATVERSE_WEB_WORKERS", "3")))
app = FastAPI(title="MatVerse Agent Local", version="1.0.0")


class TaskRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=50_000)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    workspace = html.escape(str(settings.workspace))
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MatVerse Agent Local</title>
<style>
:root{{color-scheme:dark;--bg:#070a10;--panel:#111725;--text:#f5f7ff;--muted:#9aa7bd;--accent:#65f0bd;--line:#28334b}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#172038,var(--bg) 42%);color:var(--text);font:16px/1.5 system-ui,sans-serif}}main{{width:min(100% - 2rem,1100px);margin:auto;padding:4rem 0}}header{{display:flex;justify-content:space-between;align-items:flex-start;gap:2rem;margin-bottom:2rem}}h1{{font-size:clamp(2.5rem,7vw,5.5rem);line-height:.92;margin:.25rem 0}}.eyebrow{{color:var(--accent);font-weight:900;letter-spacing:.2em}}.workspace{{color:var(--muted);word-break:break-all}}form,.task{{background:#111725dd;border:1px solid var(--line);border-radius:22px;padding:1.4rem;box-shadow:0 25px 70px #0006}}textarea{{width:100%;min-height:160px;background:#090d16;color:var(--text);border:1px solid var(--line);border-radius:14px;padding:1rem;font:inherit;resize:vertical}}button{{border:0;border-radius:12px;padding:.9rem 1.2rem;background:var(--accent);color:#06110d;font-weight:900;cursor:pointer}}.row{{display:flex;justify-content:space-between;gap:1rem;align-items:center;margin-top:1rem}}#tasks{{display:grid;gap:1rem;margin-top:2rem}}.task h2{{font-size:1rem;margin:0}}.meta{{color:var(--muted);font-family:ui-monospace,monospace;font-size:.82rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#090d16;padding:1rem;border-radius:12px;max-height:320px;overflow:auto}}.status{{color:var(--accent);font-weight:900}}@media(max-width:700px){{header,.row{{display:block}}button{{width:100%;margin-top:1rem}}}}
</style>
</head>
<body><main>
<header><div><div class="eyebrow">MATVERSE AGENT LOCAL</div><h1>Command Center</h1><div class="workspace">{workspace}</div></div><div id="health" class="status">checking</div></header>
<form id="form"><textarea id="goal" required placeholder="Descreva o objetivo completo. Ex.: audite o repositório, corrija os testes e gere um relatório com evidências."></textarea><div class="row"><span class="workspace">Autonomia governada · Ollama · MCP · receipts SHA-256</span><button type="submit">Executar missão</button></div></form>
<section id="tasks"></section>
</main><script>
const tasks=document.querySelector('#tasks');
async function refresh(){{
 const response=await fetch('/api/tasks'); const rows=await response.json();
 tasks.innerHTML=rows.map(item=>`<article class="task"><div class="row"><h2>${{escapeHtml(item.goal)}}</h2><span class="status">${{item.status}}</span></div><div class="meta">task=${{item.task_id}} · run=${{item.run_id||'-'}} · ${{item.updated_at}}</div>${{item.result?`<pre>${{escapeHtml(item.result)}}</pre>`:''}}${{item.error?`<pre>${{escapeHtml(item.error)}}</pre>`:''}}</article>`).join('');
}}
function escapeHtml(value){{return String(value).replace(/[&<>"']/g,char=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}}[char]));}}
document.querySelector('#form').addEventListener('submit',async event=>{{event.preventDefault();const goal=document.querySelector('#goal');const response=await fetch('/api/tasks',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify({{goal:goal.value}})}});if(response.ok){{goal.value='';await refresh();}}else{{alert(await response.text());}}}});
async function health(){{const r=await fetch('/api/health');const data=await r.json();document.querySelector('#health').textContent=data.status;}}
refresh();health();setInterval(refresh,2500);
</script></body></html>"""


@app.get("/api/health")
def health() -> dict[str, object]:
    try:
        ollama = OllamaClient(settings.ollama_url, settings.model).doctor()
    except OllamaError as exc:
        ollama = {"status": "BLOCK", "error": str(exc)}
    ledger_ok, ledger_message = Ledger(settings.database_path).verify()
    overall = "PASS" if ollama.get("status") == "PASS" and ledger_ok else "HOLD"
    return {
        "status": overall,
        "model": settings.model,
        "ollama": ollama,
        "ledger": {"valid": ledger_ok, "message": ledger_message},
        "network_enabled": settings.network_enabled,
    }


@app.post("/api/tasks", status_code=202)
def create_task(request: TaskRequest) -> dict[str, object]:
    record = queue.submit(request.goal)
    return record.public()


@app.get("/api/tasks")
def list_tasks(limit: int = 100) -> list[dict[str, object]]:
    bounded = max(1, min(limit, 500))
    return [record.public() for record in queue.list(bounded)]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, object]:
    try:
        return queue.get(task_id).public()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


def main() -> None:
    uvicorn.run(app, host=settings.host, port=settings.port)
