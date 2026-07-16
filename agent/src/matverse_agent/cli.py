from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .config import Settings
from .ledger import Ledger
from .ollama_client import OllamaClient, OllamaError
from .runtime import AgentRuntime


def _approval(command: str, risk: str) -> bool:
    if not sys.stdin.isatty():
        return False
    print(f"\nApproval required [{risk}]\n{command}")
    answer = input("Execute? [y/N] ").strip().lower()
    return answer in {"y", "yes", "s", "sim"}


def _settings(args: argparse.Namespace) -> Settings:
    return Settings.from_env(
        workspace=getattr(args, "workspace", None),
        approval_mode=getattr(args, "approval_mode", None),
    )


def command_init(args: argparse.Namespace) -> int:
    settings = _settings(args)
    instructions = settings.workspace / "AGENTS.md"
    if not instructions.exists():
        instructions.write_text(
            """# Workspace instructions

- Inspect before editing.
- Keep changes reversible and scoped.
- Run tests and report failures honestly.
- Never claim execution without a tool result.
- Do not store credentials in the repository.
""",
            encoding="utf-8",
        )
    policy = settings.state_dir / "policy.json"
    if not policy.exists():
        policy.write_text(
            json.dumps(
                {
                    "approval_mode": settings.approval_mode,
                    "network_enabled": settings.network_enabled,
                    "shell_enabled": settings.shell_enabled,
                    "workspace": str(settings.workspace),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(json.dumps({"status": "PASS", "workspace": str(settings.workspace)}, indent=2))
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    settings = _settings(args)
    checks: dict[str, object] = {
        "python": sys.version.split()[0],
        "workspace": str(settings.workspace),
        "git": shutil.which("git"),
        "ffmpeg": shutil.which("ffmpeg"),
        "docker": shutil.which("docker"),
        "playwright": shutil.which("playwright"),
        "network_enabled": settings.network_enabled,
        "searxng_url": settings.searxng_url,
    }
    try:
        checks["ollama"] = OllamaClient(settings.ollama_url, settings.model).doctor()
    except OllamaError as exc:
        checks["ollama"] = {"status": "BLOCK", "error": str(exc)}
    valid, message = Ledger(settings.database_path).verify()
    checks["ledger"] = {"status": "PASS" if valid else "BLOCK", "message": message}
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    ollama = checks["ollama"]
    return 0 if isinstance(ollama, dict) and ollama.get("status") == "PASS" else 1


def command_run(args: argparse.Namespace) -> int:
    settings = _settings(args)
    callback = None if settings.approval_mode == "never" else _approval
    result = AgentRuntime(settings, callback).run(args.goal)
    print(result.final)
    print(f"\nSTATUS={result.status}")
    print(f"RUN_ID={result.run_id}")
    print(f"RECEIPT={result.receipt_path}")
    return 0 if result.status == "PASS" else 1


def command_parallel(args: argparse.Namespace) -> int:
    settings = _settings(args)
    callback = None if settings.approval_mode == "never" else _approval
    results = AgentRuntime.run_parallel(
        settings,
        args.goals,
        workers=args.workers,
        approval_callback=callback,
    )
    payload = [
        {
            "run_id": result.run_id,
            "status": result.status,
            "receipt": str(result.receipt_path),
            "final": result.final,
        }
        for result in results
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if all(result.status == "PASS" for result in results) else 1


def command_verify_ledger(args: argparse.Namespace) -> int:
    settings = _settings(args)
    valid, message = Ledger(settings.database_path).verify()
    print(message)
    return 0 if valid else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="matverse-agent",
        description="Local autonomous agent with governed tools and evidence receipts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--workspace", type=Path, default=Path.cwd())
        subparser.add_argument(
            "--approval-mode",
            choices=["always", "on-risk", "never"],
            default=None,
        )

    init_parser = subparsers.add_parser("init")
    common(init_parser)
    init_parser.set_defaults(handler=command_init)

    doctor_parser = subparsers.add_parser("doctor")
    common(doctor_parser)
    doctor_parser.set_defaults(handler=command_doctor)

    run_parser = subparsers.add_parser("run")
    common(run_parser)
    run_parser.add_argument("goal")
    run_parser.set_defaults(handler=command_run)

    parallel_parser = subparsers.add_parser("parallel")
    common(parallel_parser)
    parallel_parser.add_argument("goals", nargs="+")
    parallel_parser.add_argument("--workers", type=int, default=3)
    parallel_parser.set_defaults(handler=command_parallel)

    verify_parser = subparsers.add_parser("verify-ledger")
    common(verify_parser)
    verify_parser.set_defaults(handler=command_verify_ledger)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = int(args.handler(args))
    except KeyboardInterrupt:
        code = 130
    except Exception as exc:
        print(f"BLOCK: {type(exc).__name__}: {exc}", file=sys.stderr)
        code = 1
    raise SystemExit(code)
