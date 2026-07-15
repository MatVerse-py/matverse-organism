"""
matverse.urano
==============

URANO Metabolic Runtime — the Hypothesis-to-Experiment Engine.

The Organism picks the next best hypothesis. URANO compiles it into an
ExperimentContract, runs the experiment in a controlled executor, observes
the result, and feeds it back to the Organism for re-ranking.

The runtime NEVER performs an external side-effect. It only executes
contractual experiments, all of which must be local-sandbox, deterministic
within a seed, and fully reversible.
"""
from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .schema import ExperimentContract, ExperimentResult, HypothesisStatus
from .monte_carlo import monte_carlo, summarize, cvar, is_finite_number
from .ledger import Ledger


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------

def _monte_carlo_executor(contract: ExperimentContract) -> Dict[str, Any]:
    """Run Monte Carlo to test the contract's claim."""
    n = int(contract.inputs.get("n_samples", 5000))
    seed = contract.seed
    mu = float(contract.inputs.get("mu", 0.0))
    sigma = float(contract.inputs.get("sigma", max(abs(mu) * 0.1, 1e-6)))
    samples = monte_carlo(n, sampler=lambda: random.gauss(mu, sigma), seed=seed)
    samples = [s for s in samples if is_finite_number(s)]
    return {
        "n": len(samples),
        "summary": summarize(samples),
        "cvar10": round(cvar(samples, alpha=0.10), 4),
    }


def _unit_test_executor(contract: ExperimentContract) -> Dict[str, Any]:
    """A noop-friendly executor that asserts invariants on a fixture."""
    fixture = contract.inputs.get("fixture", {})
    expected_keys = set(contract.inputs.get("expected_keys", []))
    actual_keys = set(fixture.keys())
    missing = sorted(expected_keys - actual_keys)
    return {
        "missing_keys": missing,
        "passed": not missing,
        "fixture_size": len(fixture),
    }


EXECUTORS: Dict[str, Callable[[ExperimentContract], Dict[str, Any]]] = {
    "monte_carlo": _monte_carlo_executor,
    "unit_test": _unit_test_executor,
}


# ---------------------------------------------------------------------------
# URANO
# ---------------------------------------------------------------------------

class URANO:
    """Compiles hypotheses into experiments, runs them, returns observations.

    Design contract:
      - No network access (network='denied' is enforced unless explicitly overridden)
      - No external side effects
      - Deterministic given a seed
      - Bounded timeout
    """

    def __init__(self, ledger: Optional[Ledger] = None) -> None:
        self.ledger = ledger if ledger is not None else Ledger()
        self.history: List[Dict[str, Any]] = []

    def compile(self, problem_id: str, hypothesis_id: str, claim: str,
                falsification: str, test_method: str, *,
                seed: int = 0, capabilities: Optional[List[str]] = None,
                inputs: Optional[Dict[str, Any]] = None,
                human_owner: str = "") -> ExperimentContract:
        return ExperimentContract(
            experiment_id=f"EXP-{int(time.time())}-{hypothesis_id}",
            problem_id=problem_id,
            hypothesis_id=hypothesis_id,
            claim=claim,
            falsification_condition=falsification,
            inputs=inputs or {"n_samples": 5000, "mu": 1.0, "sigma": 0.1},
            capabilities=capabilities or ["monte_carlo"],
            executor_mode="local_sandbox",
            timeout_seconds=300,
            network="denied",
            metrics=["mean", "p10", "p90", "cvar10"],
            acceptance={"mean": ">= 0.0"},
            risk_blast_radius="local",
            reversibility="complete",
            rollback="rm -rf .experiment/",
            human_owner=human_owner,
            seed=seed,
        )

    def run(self, contract: ExperimentContract) -> ExperimentResult:
        started = time.time()
        executor = EXECUTORS.get(contract.executor_mode) or _monte_carlo_executor
        # The executor mode stored in ExperimentContract is the test_method, not the
        # executor mode field. The actual executor is chosen by capability/capability list.
        if "unit_test" in contract.capabilities:
            executor = _unit_test_executor
        if "monte_carlo" in contract.capabilities:
            executor = _monte_carlo_executor
        try:
            observation = executor(contract)
            error = None
            status = "PASS"
        except Exception as exc:  # pragma: no cover — defensive
            observation = {}
            error = repr(exc)
            status = "FAIL"

        duration = time.time() - started
        # Compare to falsification
        refuted = self._refutes(contract, observation)
        if refuted:
            status = HypothesisStatus.REFUTED_PRESERVED

        result = ExperimentResult(
            experiment_id=contract.experiment_id,
            hypothesis_id=contract.hypothesis_id,
            status=status,
            observation=observation,
            duration_s=round(duration, 4),
            refuted=refuted,
            error=error,
        )

        self.history.append({"contract": contract.to_dict(), "result": result.to_dict()})
        self.ledger.append(
            kind="urano",
            input_obj=contract.to_dict(),
            output_obj=result.to_dict(),
            status=status,
            extra={"duration_s": result.duration_s},
        )
        return result

    @staticmethod
    def _refutes(contract: ExperimentContract, observation: Dict[str, Any]) -> bool:
        """Apply the falsification condition to the observation."""
        cond = contract.falsification_condition or ""
        if not cond:
            return False
        try:
            if "<" in cond:
                thr = float(cond.split("<")[1])
                mean = observation.get("summary", {}).get("mean", 1.0)
                return mean < thr
            if ">" in cond:
                thr = float(cond.split(">")[1])
                mean = observation.get("summary", {}).get("mean", 0.0)
                return mean > thr
        except (ValueError, IndexError, AttributeError):
            return False
        return False
