#!/usr/bin/env python3
"""
repo_convergence_audit.py

Audita convergência arquitetural entre repositórios irmãos usando:
- histórico recente de commits
- arquivos versionados
- palavras-chave de capacidade

Uso:
    python scripts/repo_convergence_audit.py
    python scripts/repo_convergence_audit.py --repo matverse-organism=/workspace/matverse-organism
    python scripts/repo_convergence_audit.py --pretty
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List

DEFAULT_REPOS = {
    "matverse-organism": Path("/workspace/matverse-organism"),
    "csi-organism-manager": Path("/workspace/csi-organism-manager"),
}

KEYWORDS = {
    "guardian": ["guardian", "health", "diagnostic", "recovery", "repair"],
    "observability": ["log", "ledger", "trace", "stream", "event"],
    "viability": ["viability", "fitness", "homeostasis", "stress", "coherence", "psi"],
    "cyber_physical": ["sensor", "actuator", "physical", "hardware", "gpio", "serial", "webhook"],
    "api_contract": ["api", "endpoint", "route", "state", "cells", "layers", "ledger"],
}


@dataclass
class RepoAudit:
    name: str
    path: str
    exists: bool
    latest_commits: List[str]
    tracked_files: List[str]
    keyword_hits: Dict[str, List[str]]


def run(cmd: List[str], cwd: Path) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout


def git_commits(repo: Path, n: int = 12) -> List[str]:
    out = run(["git", "log", "--oneline", f"-n{n}"], repo)
    return [line.strip() for line in out.splitlines() if line.strip()]


def git_files(repo: Path) -> List[str]:
    out = run(["git", "ls-files"], repo)
    return [line.strip() for line in out.splitlines() if line.strip()]


def search_keywords(files: Iterable[str]) -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {k: [] for k in KEYWORDS}
    for file_path in files:
        lowered = file_path.lower()
        for topic, words in KEYWORDS.items():
            if any(word in lowered for word in words):
                hits[topic].append(file_path)
    return hits


def audit_repo(name: str, path: Path) -> RepoAudit:
    if not path.exists():
        return RepoAudit(
            name=name,
            path=str(path),
            exists=False,
            latest_commits=[],
            tracked_files=[],
            keyword_hits={},
        )

    files = git_files(path)
    return RepoAudit(
        name=name,
        path=str(path),
        exists=True,
        latest_commits=git_commits(path),
        tracked_files=files,
        keyword_hits=search_keywords(files),
    )


def compare(a: RepoAudit, b: RepoAudit) -> Dict[str, object]:
    set_a = set(a.tracked_files)
    set_b = set(b.tracked_files)
    return {
        "only_in_a": sorted(set_a - set_b)[:200],
        "only_in_b": sorted(set_b - set_a)[:200],
        "common_files": sorted(set_a & set_b)[:200],
        "keyword_overlap": {
            topic: sorted(set(a.keyword_hits.get(topic, [])) & set(b.keyword_hits.get(topic, [])))
            for topic in KEYWORDS
        },
    }


def parse_repo_overrides(items: List[str]) -> Dict[str, Path]:
    overrides: Dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Formato inválido para --repo '{item}'. Use nome=/caminho.")
        name, raw_path = item.split("=", 1)
        normalized_name = name.strip()
        normalized_path = raw_path.strip()
        if not normalized_name or not normalized_path:
            raise ValueError(f"Formato inválido para --repo '{item}'. Use nome=/caminho.")
        overrides[normalized_name] = Path(normalized_path)
    return overrides


def build_recommendations(mat: RepoAudit | None, csi: RepoAudit | None) -> List[str]:
    recommendations: List[str] = []

    if not mat or not csi or not mat.exists or not csi.exists:
        return recommendations

    if mat.keyword_hits.get("api_contract") and csi.keyword_hits.get("api_contract"):
        recommendations.append("Extrair contrato comum de API e eventos para um pacote compartilhado.")
    if csi.keyword_hits.get("cyber_physical") and not mat.keyword_hits.get("cyber_physical"):
        recommendations.append("Manter cyber-physical fora do núcleo até estabilizar estado, ledger e guardian.")
    if mat.keyword_hits.get("guardian"):
        recommendations.append("Fixar Guardian como plano de controle primário do ecossistema.")
    if mat.keyword_hits.get("observability"):
        recommendations.append("Promover análise de logs a input formal de health scoring.")
    if mat.keyword_hits.get("viability"):
        recommendations.append("Versionar explicitamente a função de viabilidade para evitar deriva semântica.")

    return recommendations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita convergência entre repositórios do ecossistema MatVerse.")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Override de repositório no formato nome=/caminho. Pode ser repetido.",
    )
    parser.add_argument("--pretty", action="store_true", help="Imprime JSON com indentação.")
    args = parser.parse_args()

    repos = dict(DEFAULT_REPOS)
    repos.update(parse_repo_overrides(args.repo))

    audits = {name: audit_repo(name, path) for name, path in repos.items()}
    result: Dict[str, object] = {
        "repos": {name: asdict(audit) for name, audit in audits.items()},
        "comparison": {},
        "recommendations": [],
    }

    names = list(audits)
    if len(names) >= 2:
        first, second = names[0], names[1]
        if audits[first].exists and audits[second].exists:
            result["comparison"] = compare(audits[first], audits[second])

    mat = audits.get("matverse-organism")
    csi = audits.get("csi-organism-manager")
    result["recommendations"] = build_recommendations(mat, csi)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
