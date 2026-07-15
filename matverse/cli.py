"""
matverse.cli (v3.7.0)
====================

The full HypothesisOps CLI. Exposes every organ as a subcommand.

Top-level commands:
  hypo init <objective>               create a problem file
  hypo resolve <problem.json>         run the Organism (--execute for full cycle)
  hypo promote <learning record>      feed the Metacortex

  hypo organism run <problem.json>    run the FullOrganismRunner (v3.6.0)
  hypo organism show                  print last organism report

  hypo invariants check <problem>     enforce the 8 invariants
  hypo laws evaluate <problem>        evaluate the 8 laws
  hypo laws list                      list known law versions

  hypo cassandra interpret <problem>  produce a Cassandra reading
  hypo svca replay <svca.json>        re-run a transmutation and compare
  hypo atlas show                     show the live atlas
  hypo atlas health                   print organ states and counts

  hypo thermo record <workload.json>  add a thermodynamic record
  hypo thermo report                  aggregate over all records

  hypo captals record <mbit.json>     add an M-bit
  hypo captals report                 distribution of mbits

  hypo existential status             summary of metabolism, apoptosis,
                                       antifragility, homeostasis
  hypo mmnb show                      current MMNB
  hypo mmnb lineage                   full lineage of MNBs

  hypo closure compile <problem>      produce a closure bundle
  hypo publish prepare <closure>      produce platform metadata
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
from .laws import ConstitutionalLaws
from .invariants import Invariants, InvariantViolation
from .cassandra import Cassandra
from .svca import SVCA
from .atlas import Atlas
from .thermo import ThermoCortex
from .captals import CaptalsEngine, MBit
from .existential import Metabolism, Autopoiesis, Apoptosis, Antifragility, Homeostasis
from .closure_macro import ClosureMacroCompiler
from .publishers import prepare_publication
from .replay import Replayer
from .umjam import UMJAM, UMJAMSpec
from .capability import CapabilityRegistry
from .mmnb import MMNBStore
from .runner import FullOrganismRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Commands (v3.0)
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
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
                "evidence_for": [], "evidence_against": [],
                "falsification_criteria": "value < 0.2",
                "test_method": "monte_carlo",
                "cost_estimate": 50.0, "expected_value": 100.0,
                "risk": 0.3, "reversibility": 0.9, "lineage": [],
            } for i in range(args.n_hypotheses or 2)
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
    ledger = Ledger(path=args.ledger) if args.ledger else Ledger()
    organism = Organism(ledger=ledger, n_mc=args.n_mc, seed=args.seed)
    report = organism.investigate(problem)
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
# Commands (v3.7.0)
# ---------------------------------------------------------------------------

def cmd_organism_run(args: argparse.Namespace) -> int:
    problem = Problem.from_dict(_read_json(args.input))
    runner = FullOrganismRunner()
    out = runner.run(
        problem,
        closure_scale=args.scale or "MESO",
        closure_title=args.title,
        closure_parent=args.parent,
        repository=args.repository or "MatVerse-py/matverse-organism",
        commit=args.commit or "HEAD",
        release_tag=args.tag,
        executable=not args.no_execute,
    )
    if args.output:
        _write_json(args.output, out.to_dict())
        print(f"[hypo organism run] wrote {args.output}")
        print(f"  closure_id: {out.closure.closure_id}")
        print(f"  state: {out.closure.state_closure}")
        print(f"  epistemic: {out.closure.state_epistemic}")
        print(f"  replay: {out.replay_report['matches']}")
    else:
        print(json.dumps(out.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_organism_show(args: argparse.Namespace) -> int:
    runner = FullOrganismRunner()
    print(json.dumps(runner.organism.investigate(
        Problem.from_dict(_read_json(args.input))).to_dict(),
        indent=2, ensure_ascii=False))
    return 0


def cmd_invariants_check(args: argparse.Namespace) -> int:
    p = Problem.from_dict(_read_json(args.input))
    inv = Invariants()
    verdicts = inv.evaluate(p)
    out = {"verdicts": [v.to_dict() for v in verdicts],
           "all_hold": inv.all_hold(verdicts)}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if args.enforce and not out["all_hold"]:
        try:
            inv.enforce(p)
        except InvariantViolation as exc:
            print(f"ENFORCE-FAILED: {exc}", file=sys.stderr)
            return 1
    return 0 if out["all_hold"] else 2


def cmd_laws_evaluate(args: argparse.Namespace) -> int:
    p = Problem.from_dict(_read_json(args.input))
    laws = ConstitutionalLaws()
    verdicts = laws.evaluate(p)
    print(json.dumps({"verdicts": [v.to_dict() for v in verdicts],
                      "summary": laws.summary(verdicts)},
                     indent=2, ensure_ascii=False))
    return 0


def cmd_cassandra_interpret(args: argparse.Namespace) -> int:
    p = Problem.from_dict(_read_json(args.input))
    c = Cassandra()
    r = c.interpret(p)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_cassandra_chat(args: argparse.Namespace) -> int:
    """Conversational Cassandra — constitutional, fail-closed."""
    from .cassandra_agent import CassandraAgent
    agent = CassandraAgent(mode=args.mode or "auto")
    print(f"[mode: {agent.mode}]")
    run = agent.chat(args.message, persist=args.persist)
    print(f"[run_id: {run.run_id}]")
    print(f"[epistemic: {run.epistemic_classification}]")
    print(f"[gate: {run.gate_status}]")
    print(f"[base44: {run.used_base44}]")
    print("---")
    print(run.cassandra_response)
    return 0


def cmd_cassandra_system_prompt(args: argparse.Namespace) -> int:
    """Print the constitutional system prompt used by Cassandra."""
    from .cassandra_agent import CASSANDRA_SYSTEM_PROMPT
    print(CASSANDRA_SYSTEM_PROMPT)
    return 0


def cmd_svca_replay(args: argparse.Namespace) -> int:
    umjam = UMJAM()
    umjam.registry.register_builtins()
    svca_dict = _read_json(args.input)
    # Reconstruct a minimal SVCA from the dict
    spec = UMJAMSpec(
        operation_id=svca_dict["spec"].get("operation_id", "OP"),
        capability_id=svca_dict["capability_id"],
        inputs=svca_dict["spec"].get("inputs", {}),
        constraints=svca_dict["spec"].get("constraints", []),
        limits=svca_dict["spec"].get("limits", {}),
        seed=svca_dict["spec"].get("seed", 0),
    )
    state_in = spec.inputs
    result = umjam.transmute(spec, state_in)
    svca = SVCA.from_transmutation(spec, result, metrics={})
    report = Replayer(umjam).replay(svca, independent=args.independent)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_atlas_show(args: argparse.Namespace) -> int:
    a = Atlas()
    print(json.dumps(a.snapshot(), indent=2, ensure_ascii=False))
    return 0


def cmd_atlas_health(args: argparse.Namespace) -> int:
    a = Atlas()
    print(json.dumps(a.health(), indent=2, ensure_ascii=False))
    return 0


def cmd_thermo_record(args: argparse.Namespace) -> int:
    tc = ThermoCortex()
    workload = _read_json(args.input)
    r = tc.record(args.execution_id, workload)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_thermo_report(args: argparse.Namespace) -> int:
    tc = ThermoCortex()
    print(json.dumps(tc.summary(), indent=2, ensure_ascii=False))
    return 0


def cmd_captals_record(args: argparse.Namespace) -> int:
    data = _read_json(args.input)
    m = MBit(**data)
    e = CaptalsEngine()
    e.record(m)
    print(json.dumps(e.summary(), indent=2, ensure_ascii=False))
    return 0


def cmd_captals_report(args: argparse.Namespace) -> int:
    e = CaptalsEngine()
    print(json.dumps(e.summary(), indent=2, ensure_ascii=False))
    return 0


def cmd_existential_status(args: argparse.Namespace) -> int:
    out = {
        "metabolism": {"viability_placeholder": True,
                       "note": "instantiate MetabolismBudget for real viability"},
        "apoptosis": Apoptosis().summary(),
        "antifragility": Antifragility().summary(),
        "homeostasis": Homeostasis().summary(),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_mmnb_show(args: argparse.Namespace) -> int:
    if not args.store:
        print("error: --store is required (path to MMNB directory)", file=sys.stderr)
        return 2
    store = MMNBStore(args.store)
    cur = store.current()
    if cur is None:
        print("no MMNB found; run `hypo organism run` first", file=sys.stderr)
        return 1
    print(json.dumps(cur.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_mmnb_lineage(args: argparse.Namespace) -> int:
    if not args.store:
        print("error: --store is required", file=sys.stderr)
        return 2
    store = MMNBStore(args.store)
    print(json.dumps([m.to_dict() for m in store.all()], indent=2,
                     ensure_ascii=False))
    return 0


def cmd_closure_compile(args: argparse.Namespace) -> int:
    problem = Problem.from_dict(_read_json(args.input))
    runner = FullOrganismRunner()
    out = runner.run(problem,
                     closure_scale=args.scale or "MESO",
                     closure_title=args.title,
                     repository=args.repository or "MatVerse-py/matverse-organism",
                     commit=args.commit or "HEAD",
                     release_tag=args.tag)
    if args.output:
        _write_json(args.output, out.closure.to_dict())
        print(f"[hypo closure compile] wrote {args.output}")
    else:
        print(json.dumps(out.closure.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_publish_prepare(args: argparse.Namespace) -> int:
    closure_dict = _read_json(args.input)
    # We need a real ClosureBundle; this command accepts a dict and
    # reconstructs enough to call prepare_publication. For full
    # closure objects, use `hypo organism run` + post-process.
    from .closure_macro import (
        ClosureBundle, PaperProjection, CodeProjection,
        ExecutionProjection, CanonizationProjection, ThermoProjection,
        RegenerativeProjection,
    )
    closure = ClosureBundle(
        closure_id=closure_dict.get("closure_id", "C?"),
        parent_closure_id=closure_dict.get("parent_closure_id"),
        scale=closure_dict.get("scale", "MESO"),
        organism="matverse-organism", version=closure_dict.get("version", "3.7.0"),
        paper=PaperProjection(artifact_id="P", title=closure_dict.get("paper", {}).get("title", "?"),
                              abstract=closure_dict.get("paper", {}).get("abstract", "")),
        code=CodeProjection(repository=args.repository or "MatVerse-py/matverse-organism",
                            commit=closure_dict.get("code", {}).get("commit", "HEAD"),
                            release_tag=closure_dict.get("code", {}).get("release_tag")),
        execution=ExecutionProjection(
            run_id=closure_dict.get("execution", {}).get("run_id", "R?"),
            environment_hash="",
            receipt_hash=closure_dict.get("execution", {}).get("receipt_hash", ""),
            replay_status=closure_dict.get("execution", {}).get("replay_status", "LOCAL_REPLAYED"),
        ),
        canonization=CanonizationProjection(
            manifest_hash=closure_dict.get("canonization", {}).get("manifest_hash", ""),
            merkle_root=closure_dict.get("canonization", {}).get("merkle_root", ""),
            gate_state=closure_dict.get("canonization", {}).get("gate_state", "CLOSED"),
        ),
        thermo=ThermoProjection(),
        regenerative=RegenerativeProjection(),
    )
    ps = prepare_publication(
        bundle=closure,
        creators=[{"name": args.creator or "MatVerse Builder"}],
        github_repo=args.repository or "MatVerse-py/matverse-organism",
        github_tag=closure.code.release_tag or "v3.7.0",
        hf_repo_id=args.hf_repo or f"matverse/{closure.closure_id.lower()}",
    )
    if args.output:
        _write_json(args.output, ps.to_dict())
        print(f"[hypo publish prepare] wrote {args.output}")
    else:
        print(json.dumps(ps.to_dict(), indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hypo", description=f"MatVerse HypothesisOps CLI v{__version__}",
    )
    p.add_argument("--version", action="version", version=f"hypo {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # ----- v3.0 -----
    p_init = sub.add_parser("init", help="Create a hypothesis file from a problem description")
    p_init.add_argument("--objective", required=True)
    p_init.add_argument("--scope", help="Scope qualifier")
    p_init.add_argument("--id")
    p_init.add_argument("--n-hypotheses", type=int, default=2)
    p_init.add_argument("--constraint", action="append")
    p_init.add_argument("--stakeholder", action="append")
    p_init.add_argument("--science-origin")
    p_init.add_argument("--contract")
    p_init.add_argument("--ecosystem-impact")
    p_init.add_argument("-o", "--output")
    p_init.set_defaults(func=cmd_init)

    p_res = sub.add_parser("resolve", help="Run the Organism on a problem file")
    p_res.add_argument("-i", "--input", required=True)
    p_res.add_argument("-o", "--output")
    p_res.add_argument("--seed", type=int, default=20260714)
    p_res.add_argument("--n-mc", type=int, default=5000)
    p_res.add_argument("--execute", action="store_true")
    p_res.add_argument("--ledger")
    p_res.set_defaults(func=cmd_resolve)

    p_prom = sub.add_parser("promote", help="Send a learning record to the Metacortex")
    p_prom.add_argument("-i", "--input")
    p_prom.add_argument("--problem-class")
    p_prom.add_argument("--strategy")
    p_prom.add_argument("--lenses")
    p_prom.add_argument("--n-mc", type=int)
    p_prom.add_argument("--seed", type=int)
    p_prom.add_argument("--outcome", choices=["PASS", "FAIL", "REFUTED_PRESERVED", "UNDERDETERMINED"])
    p_prom.add_argument("--time", type=float)
    p_prom.add_argument("--predicted", type=float)
    p_prom.add_argument("--observed", type=float)
    p_prom.add_argument("--ledger")
    p_prom.add_argument("-o", "--output")
    p_prom.set_defaults(func=cmd_promote)

    # ----- v3.7.0 -----
    p_org = sub.add_parser("organism", help="Run the FullOrganismRunner (v3.6+)")
    org_sub = p_org.add_subparsers(dest="organism_command", required=True)
    p_org_run = org_sub.add_parser("run", help="Run the full organism on a problem")
    p_org_run.add_argument("-i", "--input", required=True)
    p_org_run.add_argument("-o", "--output")
    p_org_run.add_argument("--scale", choices=["MICRO", "MESO", "MACRO"])
    p_org_run.add_argument("--title")
    p_org_run.add_argument("--parent")
    p_org_run.add_argument("--repository")
    p_org_run.add_argument("--commit")
    p_org_run.add_argument("--tag")
    p_org_run.add_argument("--no-execute", action="store_true")
    p_org_run.set_defaults(func=cmd_organism_run)
    p_org_show = org_sub.add_parser("show", help="Show the organism's report on a problem")
    p_org_show.add_argument("-i", "--input", required=True)
    p_org_show.set_defaults(func=cmd_organism_show)

    p_inv = sub.add_parser("invariants", help="Invariants engine")
    inv_sub = p_inv.add_subparsers(dest="invariants_command", required=True)
    p_inv_check = inv_sub.add_parser("check", help="Evaluate the 8 invariants on a problem")
    p_inv_check.add_argument("-i", "--input", required=True)
    p_inv_check.add_argument("--enforce", action="store_true")
    p_inv_check.set_defaults(func=cmd_invariants_check)

    p_laws = sub.add_parser("laws", help="Constitutional laws")
    laws_sub = p_laws.add_subparsers(dest="laws_command", required=True)
    p_laws_eval = laws_sub.add_parser("evaluate", help="Evaluate the 8 laws on a problem")
    p_laws_eval.add_argument("-i", "--input", required=True)
    p_laws_eval.set_defaults(func=cmd_laws_evaluate)
    p_laws_list = laws_sub.add_parser("list", help="List known law versions (placeholder)")
    p_laws_list.set_defaults(func=lambda a: (print(json.dumps({"laws": "v1"}, indent=2)), 0)[1])

    p_cas = sub.add_parser("cassandra", help="Cassandra cognitive layer")
    cas_sub = p_cas.add_subparsers(dest="cassandra_command", required=True)
    p_cas_int = cas_sub.add_parser("interpret", help="Interpret a problem")
    p_cas_int.add_argument("-i", "--input", required=True)
    p_cas_int.set_defaults(func=cmd_cassandra_interpret)
    p_cas_chat = cas_sub.add_parser("chat", help="Conversational Cassandra (constitutional, fail-closed)")
    p_cas_chat.add_argument("message", help="User message to Cassandra")
    p_cas_chat.add_argument("--mode", choices=["auto", "standalone", "base44"], default="auto",
                            help="Agent mode (default: auto-detect from BASE44_API_KEY env var)")
    p_cas_chat.add_argument("--persist", action="store_true",
                            help="Persist the run to Base44 (only works in base44 mode)")
    p_cas_chat.set_defaults(func=cmd_cassandra_chat)
    p_cas_prompt = cas_sub.add_parser("prompt", help="Print the constitutional system prompt")
    p_cas_prompt.set_defaults(func=cmd_cassandra_system_prompt)

    p_svca = sub.add_parser("svca", help="SVCA proof capsule")
    svca_sub = p_svca.add_subparsers(dest="svca_command", required=True)
    p_svca_repl = svca_sub.add_parser("replay", help="Re-run a SVCA's transmutation")
    p_svca_repl.add_argument("-i", "--input", required=True)
    p_svca_repl.add_argument("--independent", action="store_true")
    p_svca_repl.set_defaults(func=cmd_svca_replay)

    p_atlas = sub.add_parser("atlas", help="Atlas cartographic projection")
    atlas_sub = p_atlas.add_subparsers(dest="atlas_command", required=True)
    p_atlas_show = atlas_sub.add_parser("show", help="Show the atlas snapshot")
    p_atlas_show.set_defaults(func=cmd_atlas_show)
    p_atlas_health = atlas_sub.add_parser("health", help="Show the atlas health")
    p_atlas_health.set_defaults(func=cmd_atlas_health)

    p_thermo = sub.add_parser("thermo", help="ThermoCortex")
    thermo_sub = p_thermo.add_subparsers(dest="thermo_command", required=True)
    p_thermo_rec = thermo_sub.add_parser("record", help="Record a thermodynamic measurement")
    p_thermo_rec.add_argument("-i", "--input", required=True)
    p_thermo_rec.add_argument("--execution-id", required=True)
    p_thermo_rec.set_defaults(func=cmd_thermo_record)
    p_thermo_rep = thermo_sub.add_parser("report", help="Aggregate report")
    p_thermo_rep.set_defaults(func=cmd_thermo_report)

    p_capt = sub.add_parser("captals", help="Captals engine")
    capt_sub = p_capt.add_subparsers(dest="captals_command", required=True)
    p_capt_rec = capt_sub.add_parser("record", help="Record an M-bit")
    p_capt_rec.add_argument("-i", "--input", required=True)
    p_capt_rec.set_defaults(func=cmd_captals_record)
    p_capt_rep = capt_sub.add_parser("report", help="Summary of the captals engine")
    p_capt_rep.set_defaults(func=cmd_captals_report)

    p_ex = sub.add_parser("existential", help="Existential processes")
    ex_sub = p_ex.add_subparsers(dest="existential_command", required=True)
    p_ex_status = ex_sub.add_parser("status", help="Status of all existential processes")
    p_ex_status.set_defaults(func=cmd_existential_status)

    p_mmnb = sub.add_parser("mmnb", help="MMNB causal memory")
    mmnb_sub = p_mmnb.add_subparsers(dest="mmnb_command", required=True)
    p_mmnb_show = mmnb_sub.add_parser("show", help="Show the current MMNB")
    p_mmnb_show.add_argument("--store", required=True)
    p_mmnb_show.set_defaults(func=cmd_mmnb_show)
    p_mmnb_lin = mmnb_sub.add_parser("lineage", help="Show the full MMNB lineage")
    p_mmnb_lin.add_argument("--store", required=True)
    p_mmnb_lin.set_defaults(func=cmd_mmnb_lineage)

    p_closure = sub.add_parser("closure", help="Closure compiler")
    closure_sub = p_closure.add_subparsers(dest="closure_command", required=True)
    p_closure_compile = closure_sub.add_parser("compile", help="Compile a closure for a problem")
    p_closure_compile.add_argument("-i", "--input", required=True)
    p_closure_compile.add_argument("-o", "--output")
    p_closure_compile.add_argument("--scale", choices=["MICRO", "MESO", "MACRO"])
    p_closure_compile.add_argument("--title")
    p_closure_compile.add_argument("--repository")
    p_closure_compile.add_argument("--commit")
    p_closure_compile.add_argument("--tag")
    p_closure_compile.set_defaults(func=cmd_closure_compile)

    p_pub = sub.add_parser("publish", help="Publication layer")
    pub_sub = p_pub.add_subparsers(dest="publish_command", required=True)
    p_pub_prep = pub_sub.add_parser("prepare", help="Prepare platform metadata")
    p_pub_prep.add_argument("-i", "--input", required=True, help="Closure dict (JSON)")
    p_pub_prep.add_argument("-o", "--output")
    p_pub_prep.add_argument("--repository", help="GitHub repository")
    p_pub_prep.add_argument("--creator", help="Creator name")
    p_pub_prep.add_argument("--hf-repo", help="HuggingFace repo id")
    p_pub_prep.set_defaults(func=cmd_publish_prepare)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
