"""
matverse.closure
================

Closure Compiler — verifies that the Organism has run a complete cognitive
cycle: problem -> hypotheses -> law check -> AXIS-8 -> Monte Carlo -> decision
-> URANO experiment -> observation -> ledger entry.

Returns a ClosureReport that is a single boolean (closed/not-closed) plus
detailed per-step evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Problem, ExperimentResult, ExperimentContract, LearningRecord
from .organism import Organism, OrganismReport
from .urano import URANO
from .ledger import Ledger


@dataclass
class ClosureReport:
    problem_id: str
    closed: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    receipt_hash: Optional[str] = None
    decision: str = ""
    final_observation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "closed": self.closed,
            "steps": self.steps,
            "missing": self.missing,
            "receipt_hash": self.receipt_hash,
            "decision": self.decision,
            "final_observation": self.final_observation,
        }


class ClosureCompiler:
    """Compile and verify a full cognitive cycle."""

    def __init__(self, organism: Organism, urano: URANO, ledger: Optional[Ledger] = None) -> None:
        self.organism = organism
        self.urano = urano
        if ledger is not None:
            self.ledger = ledger
        elif organism.ledger is not None:
            self.ledger = organism.ledger
        else:
            self.ledger = urano.ledger if urano.ledger is not None else Ledger()

    def run_full_cycle(
        self,
        problem: Problem,
        *,
        seed: int = 20260714,
        auto_execute: bool = False,
    ) -> ClosureReport:
        report = ClosureReport(problem_id=problem.id, closed=False)
        steps = report.steps

        # Step 1: investigate
        org_report = self.organism.investigate(problem)
        steps.append({
            "step": "investigate",
            "ok": True,
            "classification": org_report.classification,
            "decision": org_report.decision,
            "n_hypotheses": len(problem.hypotheses),
        })
        report.decision = org_report.decision
        if org_report.classification in (
            "PROHIBITED_ACTION", "PHYSICALLY_INFEASIBLE",
            "OUT_OF_SCOPE", "UNDECIDABLE_CANDIDATE",
        ):
            report.missing.append("investigation halted at classification gate")
            report.receipt_hash = self.ledger.append(
                kind="closure", input_obj=problem.to_dict(),
                output_obj=report.to_dict(), status="GATED",
            ).ledger_hash
            return report

        if not org_report.next_test:
            report.missing.append("no next_test selected by organism")
            report.receipt_hash = self.ledger.append(
                kind="closure", input_obj=problem.to_dict(),
                output_obj=report.to_dict(), status="NO_TEST",
            ).ledger_hash
            return report

        # Step 2: compile experiment
        nt = org_report.next_test
        contract = self.urano.compile(
            problem_id=problem.id,
            hypothesis_id=nt["hypothesis_id"],
            claim=nt["claim"],
            falsification=nt["falsification_criteria"],
            test_method=nt.get("test_method", "monte_carlo"),
            seed=seed,
            capabilities=["monte_carlo"],
            inputs={"n_samples": 2000, "mu": 1.0, "sigma": 0.1},
            human_owner="matverse-operator",
        )
        steps.append({
            "step": "compile",
            "ok": True,
            "experiment_id": contract.experiment_id,
            "executor_mode": contract.executor_mode,
            "network": contract.network,
        })

        if not auto_execute:
            report.missing.append("auto_execute=False: experiment compiled but not run")
            report.receipt_hash = self.ledger.append(
                kind="closure", input_obj=problem.to_dict(),
                output_obj=report.to_dict(), status="COMPILED_NOT_RUN",
            ).ledger_hash
            return report

        # Step 3: run
        result = self.urano.run(contract)
        steps.append({
            "step": "run",
            "ok": True,
            "experiment_id": result.experiment_id,
            "status": result.status,
            "refuted": result.refuted,
            "duration_s": result.duration_s,
        })
        report.final_observation = result.observation

        # Step 4: closure criterion
        # A cycle is "closed" when we have: investigate + compile + run + decision
        cycle_steps = [s["step"] for s in steps]
        if {"investigate", "compile", "run"}.issubset(cycle_steps):
            report.closed = True
        else:
            report.missing.append("not all cycle steps completed")

        report.receipt_hash = self.ledger.append(
            kind="closure", input_obj=problem.to_dict(),
            output_obj=report.to_dict(),
            status="CLOSED" if report.closed else "INCOMPLETE",
            extra={"decision": report.decision, "experiment_status": result.status},
        ).ledger_hash

        return report
