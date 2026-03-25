#!/usr/bin/env python3
"""
analyze_matverse_logs.py

Uso:
    python scripts/analyze_matverse_logs.py logs.txt
    cat logs.txt | python scripts/analyze_matverse_logs.py

Saída:
    JSON estruturado com:
    - status do frontend/backend
    - endpoints observados
    - métricas de latência
    - conexões abortadas
    - suspeita de duplicação de blocos
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


LOG_HEADER_RE = re.compile(
    r"^\[(?P<ts>\d{2}:\d{2}:\d{2}\.\d{3})\]\s+(?P<level>[A-Z]+)\s+\((?P<pid>\d+)\):\s+(?P<msg>.+)$"
)
PORT_RE = re.compile(r"port:\s*(?P<port>\d+)")
URL_RE = re.compile(r"(https?://[^\s]+)")
METHOD_RE = re.compile(r'"method":\s*"(?P<method>[A-Z]+)"')
URL_FIELD_RE = re.compile(r'"url":\s*"(?P<url>[^"]+)"')
REQ_ID_RE = re.compile(r'"id":\s*(?P<id>\d+)')
STATUS_RE = re.compile(r'"statusCode":\s*(?P<status>\d{3})')
RESP_TIME_RE = re.compile(r"responseTime:\s*(?P<rt>\d+)")
VITE_READY_RE = re.compile(r"VITE v[\d\.]+\s+ready")
SERVER_LISTENING_RE = re.compile(r"Server listening")
KERNEL_ALIVE_RE = re.compile(r"Organism kernel alive")


@dataclass
class RequestEvent:
    ts: str
    pid: int
    level: str
    event: str
    req_id: Optional[int]
    method: Optional[str]
    url: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[int]


def read_input(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def chunk_log_entries(text: str) -> List[str]:
    lines = text.splitlines()
    entries: List[str] = []
    current: List[str] = []

    for line in lines:
        if LOG_HEADER_RE.match(line):
            if current:
                entries.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)

    if current:
        entries.append("\n".join(current))

    return entries


def parse_request_entry(entry: str) -> Optional[RequestEvent]:
    header = entry.splitlines()[0]
    match = LOG_HEADER_RE.match(header)
    if not match:
        return None

    msg = match.group("msg")
    if msg not in ("request completed", "request aborted"):
        return None

    id_match = REQ_ID_RE.search(entry)
    method_match = METHOD_RE.search(entry)
    url_match = URL_FIELD_RE.search(entry)
    status_match = STATUS_RE.search(entry)
    rt_match = RESP_TIME_RE.search(entry)

    return RequestEvent(
        ts=match.group("ts"),
        pid=int(match.group("pid")),
        level=match.group("level"),
        event=msg,
        req_id=int(id_match.group("id")) if id_match else None,
        method=method_match.group("method") if method_match else None,
        url=url_match.group("url") if url_match else None,
        status_code=int(status_match.group("status")) if status_match else None,
        response_time_ms=int(rt_match.group("rt")) if rt_match else None,
    )


def summarize(text: str) -> Dict[str, Any]:
    entries = chunk_log_entries(text)
    request_events: List[RequestEvent] = []

    vite_ready = bool(VITE_READY_RE.search(text))
    vite_urls = URL_RE.findall(text)

    backend_ports: List[int] = []
    pids = set()
    kernel_alive_count = 0

    for entry in entries:
        header = entry.splitlines()[0]
        header_match = LOG_HEADER_RE.match(header)
        if header_match:
            pids.add(int(header_match.group("pid")))
            if SERVER_LISTENING_RE.search(entry):
                port_match = PORT_RE.search(entry)
                if port_match:
                    backend_ports.append(int(port_match.group("port")))
            if KERNEL_ALIVE_RE.search(entry):
                kernel_alive_count += 1

        req = parse_request_entry(entry)
        if req:
            request_events.append(req)

    completed = [r for r in request_events if r.event == "request completed"]
    aborted = [r for r in request_events if r.event == "request aborted"]

    latencies = [r.response_time_ms for r in completed if r.response_time_ms is not None]
    endpoint_counts = Counter(r.url for r in request_events if r.url)

    duplicate_blocks = False
    raw = text.strip()
    if raw:
        half = len(raw) // 2
        duplicate_blocks = raw[:half] == raw[-half:] if half else False
        if not duplicate_blocks:
            sigs = [
                (r.ts, r.pid, r.req_id, r.method, r.url, r.status_code, r.response_time_ms, r.event)
                for r in request_events
            ]
            if len(sigs) >= 2:
                counts = Counter(sigs)
                duplicate_blocks = any(count > 1 for count in counts.values())

    latency_summary: Dict[str, Any] = {
        "count": len(latencies),
        "min_ms": min(latencies) if latencies else None,
        "max_ms": max(latencies) if latencies else None,
        "mean_ms": round(statistics.mean(latencies), 3) if latencies else None,
        "median_ms": round(statistics.median(latencies), 3) if latencies else None,
    }

    health_flags = {
        "frontend_vite_ready": vite_ready,
        "backend_listening": len(backend_ports) > 0,
        "kernel_alive_seen": kernel_alive_count > 0,
        "any_5xx": any((r.status_code or 0) >= 500 for r in request_events),
        "stream_aborted_seen": any(r.url == "/api/organism/stream" for r in aborted),
        "suspected_duplicate_output": duplicate_blocks,
    }

    diagnosis = []
    if health_flags["frontend_vite_ready"]:
        diagnosis.append("frontend_up")
    if health_flags["backend_listening"]:
        diagnosis.append("backend_up")
    if health_flags["kernel_alive_seen"]:
        diagnosis.append("kernel_alive")
    if health_flags["stream_aborted_seen"] and not health_flags["any_5xx"]:
        diagnosis.append("sse_abort_likely_client_or_timeout")
    if health_flags["suspected_duplicate_output"]:
        diagnosis.append("duplicated_log_capture")

    return {
        "summary": {
            "frontend_urls": vite_urls,
            "backend_ports": sorted(set(backend_ports)),
            "pids": sorted(pids),
            "kernel_alive_count": kernel_alive_count,
            "request_event_count": len(request_events),
            "completed_request_count": len(completed),
            "aborted_request_count": len(aborted),
            "endpoint_counts": dict(endpoint_counts),
            "latency": latency_summary,
        },
        "health_flags": health_flags,
        "aborted_requests": [asdict(r) for r in aborted],
        "diagnosis": diagnosis,
        "all_requests": [asdict(r) for r in request_events],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisa logs do MatVerse/API server.")
    parser.add_argument("path", nargs="?", default=None, help="Arquivo de log. Se omitido, lê stdin.")
    parser.add_argument("--pretty", action="store_true", help="Imprime JSON formatado com indentação.")
    args = parser.parse_args()

    try:
        text = read_input(args.path)
        if not text.strip():
            raise ValueError("Entrada de log vazia.")

        result = summarize(text)
        if args.pretty:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        error = {"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
