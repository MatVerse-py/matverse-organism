# MatVerse Agent Local

Agente autônomo local, gratuito e governado para pesquisa, programação, automação e geração de artefatos. O projeto cobre as classes funcionais de AgentGPT, Manus e Codex sem depender obrigatoriamente de APIs pagas.

## Capacidades

- planejamento e decomposição iterativa de objetivos;
- loop multi-turn de ferramentas com Ollama;
- leitura, busca, escrita e edição confinadas ao workspace;
- terminal, testes, linters, Git e worktrees;
- pesquisa web por SearXNG local e acesso HTTP governado;
- memória SQLite e ledger SHA-256 encadeado;
- execução paralela de agentes em workspaces isolados;
- servidor MCP para uso por clientes compatíveis;
- interface web local;
- geração determinística de sites estáticos, PWA instalável, PPTX e vídeos MP4;
- recibos por execução com comandos, resultados, hashes e estado final.

## Limites honestos

O sistema replica funções, não modelos proprietários. A qualidade depende do modelo local, hardware, ferramentas instaladas e dados fornecidos. Vídeo é montado localmente com Pillow e FFmpeg; geração visual neural exige um servidor local adicional, como ComfyUI. Aplicativos móveis são gerados como PWA instalável; empacotamento APK pode ser feito depois com Capacitor ou Bubblewrap.

## Requisitos

- Python 3.11+
- Ollama
- modelo local com tool calling, por exemplo `qwen3:4b`
- opcional: Docker, SearXNG, FFmpeg, Playwright, Git

Para máquinas com pouca memória, use `qwen3:1.7b`. Para maior qualidade, use uma variante maior compatível com o hardware.

## Instalação

```bash
cd agent
python -m venv .venv
. .venv/bin/activate
pip install -e '.[artifacts,browser,dev]'
ollama pull qwen3:4b
cp .env.example .env
matverse-agent doctor
```

Windows PowerShell:

```powershell
cd agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[artifacts,browser,dev]"
ollama pull qwen3:4b
Copy-Item .env.example .env
matverse-agent doctor
```

## Uso

Inicializar um workspace:

```bash
matverse-agent init ./workspace
```

Executar um objetivo:

```bash
matverse-agent run \
  --workspace ./workspace \
  "Audite o projeto, corrija os testes e gere um relatório final"
```

Executar múltiplos objetivos em paralelo:

```bash
matverse-agent parallel --workspace ./workspace \
  "revise segurança" \
  "melhore documentação" \
  "execute testes"
```

Interface web:

```bash
matverse-agent-web --workspace ./workspace
```

Servidor MCP:

```bash
matverse-agent-mcp --workspace ./workspace
```

O endpoint padrão é `http://127.0.0.1:8000/mcp`.

## Pesquisa local gratuita

Suba o SearXNG opcional:

```bash
docker compose up -d searxng
```

Defina:

```bash
MATVERSE_SEARXNG_URL=http://127.0.0.1:8080
MATVERSE_NETWORK_ENABLED=1
```

## Política de execução

A autorização do proprietário habilita as classes de ferramenta, mas não remove contenção técnica:

- caminhos ficam confinados ao workspace;
- comandos destrutivos globais são sempre bloqueados;
- rede é desativada por padrão;
- segredos não são registrados integralmente;
- comandos e resultados entram no ledger;
- saída de terminal é limitada;
- cada execução tem número máximo de passos e timeout;
- `--approval-mode never` permite comandos normais sem confirmação, mas continua respeitando bloqueios constitucionais.

Modos:

- `on-risk`: solicita aprovação para ações classificadas como elevadas;
- `never`: executa ações permitidas sem perguntas;
- `always`: solicita aprovação para toda ação com efeito colateral.

## Arquitetura

```text
Goal
  -> Runtime/Planner
  -> Ollama tool-calling loop
  -> Policy Gate
  -> Tool Registry
       -> filesystem
       -> terminal/git/tests
       -> HTTP/SearXNG/browser
       -> website/PWA/slides/video
       -> MCP connectors
  -> Verification
  -> SQLite Memory + Hash Ledger + Receipt
```

## Evidência

Cada run grava em `.matverse/runs/<run_id>/`:

- `request.json`
- `messages.json`
- `result.md`
- `receipt.json`

O banco `.matverse/state.db` mantém eventos encadeados. Verifique:

```bash
matverse-agent verify-ledger --workspace ./workspace
```

## Desenvolvimento

```bash
pytest
ruff check .
mypy src
```

A branch foi criada isoladamente para revisão. Não faça merge antes de o CI passar e de uma revisão manual dos comandos permitidos.