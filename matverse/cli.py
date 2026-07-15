"""
matverse.cli
============

Command line interface. Implements the three commands of the HypothesisOps
wedge:

    hypo init       Create a hypothesis.yaml from text
    hypo resolve    Run the Organism on a hypothesis file
    hypo promote    Send a learning record to the Metacortex

The CLI is intentionally small. Everything heavy lives in the library.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Any, Dict

from . import __version__
from .schema import Problem, Hypothesis, LearningRecord
from .organism import Organism
from .urano import URANO
from .closure import ClosureCompiler
from .metacortex import Metacortex
from .ledger import Ledger


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    """Create a hypothesis YAML/JSON file from a free-text problem description."""
    problem = {
        "id": args.id or f"PROB-{int(time.time())}",
        "objective": args.objective,
        "scope": args.scope or "general",
        "constraints": args.constraint or [],
        "stakeholders": args.stakeholder or [],
        "hypotheses": [
            {
                "id": f"H-{i + 1}",
                "claim": f"Auto-generated hypothesis #{i + 1} for: {args.objective}",
                "variables": {"value": 0.5},
                "evidence_for": [],
                "evidence_against": [],
                "falsification_criteria": "value < 0.2",
                "test_method": "monte_carlo",
                "cost_estimate": 50.0,
                "expected_value": 100.0,
                "risk": 0.3,
                "reversibility": 0.9,
                "lineage": [],
            }
            for i in range(args.n_hypotheses or 2)
        ],
        "metadata": {
            "science_origin": args.science_origin or "user-stated",
            "contract": args.contract or "yaml-input",
            "ecosystem_impact": args.ecosystem_impact or "to-be-evaluated",
        },
    }
    out_path = args.output or f"{problem['id']}.json"
    _write_json(out_path, problem)
    print(f"[hypo init] wrote {out_path}")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    problem_dict = _read_json(args.input)
    problem = Problem.from_dict(problem_dict)

    ledger_path = args.ledger
    ledger = Ledger(path=ledger_path) if ledger_path else Ledger()
    organism = Organism(ledger=ledger, n_mc=args.n_mc, seed=args.seed)
    report = organism.investigate(problem)

    if args.execute:
        urano = URANO(ledger=ledger)
        closure = ClosureCompiler(organism, urano, ledger=ledger)
        full = closure.run_full_cycle(problem, seed=args.seed, auto_execute=True)
        out = {
            "organism_report": report.to_dict(),
            "closure_report": full.to_dict(),
            "ledger_verification": ledger.verify(),
        }
    else:
        out = {
            "organism_report": report.to_dict(),
            "ledger_verification": ledger.verify(),
        }

    if args.output:
        _write_json(args.output, out)
        print(f"[hypo resolve] wrote {args.output}")
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    """Send a learning record to the Metacortex and print the recommendation."""
    if args.input:
        data = _read_json(args.input)
    else:
        data = {
            "timestamp": int(time.time()),
            "problem_class": args.problem_class or "default",
            "strategy": args.strategy or "default",
            "lenses_used": args.lenses.split(",") if args.lenses else [],
            "monte_carlo_n": args.n_mc or 5000,
            "seed": args.seed or 0,
            "outcome": args.outcome or "PASS",
            "time_to_decision_s": args.time or 1.0,
            "predicted_probability": args.predicted or 0.7,
            "observed_outcome_value": args.observed,
        }

    rec = LearningRecord.from_dict(data)
    ledger = Ledger(path=args.ledger) if args.ledger else Ledger()
    ledger.load()
    meta = Metacortex(ledger=ledger)
    meta.record(rec)
    summary = meta.summary()
    rec_for_class = meta.recommend(rec.problem_class)

    out = {
        "recorded": rec.to_dict(),
        "metacortex_summary": summary,
        "recommendation": rec_for_class.to_dict() if rec_for_class else None,
    }

    if args.output:
        _write_json(args.output, out)
        print(f"[hypo promote] wrote {args.output}")
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hypo",
        description="MatVerse HypothesisOps CLI (v3.0.0)",
    )
    p.add_argument("--version", action="version", version=f"hypo {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Create a hypothesis file from a problem description")
    p_init.add_argument("--objective", required=True, help="One-sentence problem statement")
    p_init.add_argument("--scope", help="Scope qualifier")
    p_init.add_argument("--id", help="Problem id (default: PROB-<ts>)")
    p_init.add_argument("--n-hypotheses", type=int, default=2)
    p_init.add_argument("--constraint", action="append", help="Constraint (repeatable)")
    p_init.add_argument("--stakeholder", action="append", help="Stakeholder (repeatable)")
    p_init.add_argument("--science-origin", help="Science origin reference")
    p_init.add_argument("--contract", help="Contract / interface reference")
    p_init.add_argument("--ecosystem-impact", help="Ecosystem impact statement")
    p_init.add_argument("-o", "--output", help="Output path")
    p_init.set_defaults(func=cmd_init)

    # resolve
    p_res = sub.add_parser("resolve", help="Run the Organism on a problem file")
    p_res.add_argument("-i", "--input", required=True, help="Path to problem JSON")
    p_res.add_argument("-o", "--output", help="Output path (default: stdout)")
    p_res.add_argument("--seed", type=int, default=20260714)
    p_res.add_argument("--n-mc", type=int, default=5000)
    p_res.add_argument("--execute", action="store_true",
                       help="Also run URANO + ClosureCompiler (full cycle)")
    p_res.add_argument("--ledger", help="Path to ledger JSONL")
    p_res.set_defaults(func=cmd_resolve)

    # promote
    p_prom = sub.add_parser("promote", help="Send a learning record to the Metacortex")
    p_prom.add_argument("-i", "--input", help="Path to a learning_record JSON")
    p_prom.add_argument("--problem-class", help="Problem class (e.g. CLI_adoption)")
    p_prom.add_argument("--strategy", help="Strategy used (e.g. concrete_first)")
    p_prom.add_argument("--lenses", help="Comma-separated lens list")
    p_prom.add_argument("--n-mc", type=int, help="Monte Carlo sample count")
    p_prom.add_argument("--seed", type=int, help="RNG seed")
    p_prom.add_argument("--outcome", choices=["PASS", "FAIL", "REFUTED_PRESERVED", "UNDERDETERMINED"])
    p_prom.add_argument("--time", type=float, help="Time to decision in seconds")
    p_prom.add_argument("--predicted", type=float, help="Predicted probability")
    p_prom.add_argument("--observed", type=float, help="Observed outcome value")
    p_prom.add_argument("--ledger", help="Path to metacortex ledger")
    p_prom.add_argument("-o", "--output", help="Output path")
    p_prom.set_defaults(func=cmd_promote)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
