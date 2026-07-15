"""
matverse.schema
===============

JSON Schema definitions for Problem, Hypothesis, Experiment, and LearningRecord.

The schema module is the contract between the Organism and any external caller
(CLI, GitHub Action, REST API, agent, human). The same Python data classes are
used internally and exposed as JSON over the wire.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------

@dataclass
class Problem:
    """A problem as admitted to the Campo de Hipóteses."""
    id: str
    objective: str
    scope: str
    constraints: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    hypotheses: List["Hypothesis"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["hypotheses"] = [h.to_dict() for h in self.hypotheses]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Problem":
        hyps = [Hypothesis.from_dict(h) for h in data.get("hypotheses", [])]
        return cls(
            id=data["id"],
            objective=data["objective"],
            scope=data["scope"],
            constraints=data.get("constraints", []),
            stakeholders=data.get("stakeholders", []),
            hypotheses=hyps,
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------

class HypothesisStatus:
    OPEN = "OPEN_FOR_INVESTIGATION"
    TESTED = "TESTED"
    SUPPORTED = "SUPPORTED"
    REFUTED_PRESERVED = "REFUTED_PRESERVED"
    PROMOTED = "PROMOTED_TO_SKILL"
    UNDERDETERMINED = "UNDERDETERMINED"
    INTRACTABLE = "INTRACTABLE"
    UNDECIDABLE = "UNDECIDABLE_CANDIDATE"
    INFEASIBLE = "PHYSICALLY_INFEASIBLE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    PROHIBITED = "PROHIBITED_ACTION"
    HOLD = "HOLD_ACTION"
    TEST_NEXT = "TEST_NEXT"
    HUMAN_REVIEW = "HUMAN_REVIEW_CANDIDATE"


@dataclass
class Hypothesis:
    id: str
    claim: str
    variables: Dict[str, float] = field(default_factory=dict)
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    falsification_criteria: str = ""
    test_method: str = "monte_carlo"
    cost_estimate: float = 0.0
    expected_value: float = 0.0
    risk: float = 0.5
    reversibility: float = 1.0
    status: str = HypothesisStatus.OPEN
    lineage: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        # Strip unknown keys gracefully so forward-compat is preserved
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


# ---------------------------------------------------------------------------
# Experiment Contract (URANO)
# ---------------------------------------------------------------------------

@dataclass
class ExperimentContract:
    """Describes a planned experiment that turns a hypothesis into evidence."""
    experiment_id: str
    problem_id: str
    hypothesis_id: str
    claim: str
    falsification_condition: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    executor_mode: str = "local_sandbox"  # local_sandbox | monte_carlo | human_trial
    timeout_seconds: int = 300
    network: str = "denied"               # denied | readonly | open
    metrics: List[str] = field(default_factory=list)
    acceptance: Dict[str, str] = field(default_factory=dict)
    risk_blast_radius: str = "local"
    reversibility: str = "complete"
    rollback: str = ""
    human_owner: str = ""
    seed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentContract":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


# ---------------------------------------------------------------------------
# Experiment Result (URANO)
# ---------------------------------------------------------------------------

@dataclass
class ExperimentResult:
    experiment_id: str
    hypothesis_id: str
    status: str                  # PASS | FAIL | REFUTED_PRESERVED
    observation: Dict[str, Any] = field(default_factory=dict)
    duration_s: float = 0.0
    refuted: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


# ---------------------------------------------------------------------------
# Learning Record (Metacortex)
# ---------------------------------------------------------------------------

@dataclass
class LearningRecord:
    """A record of how the organism solved a problem, used by the Metacortex
    to extract methods (level-3 learning: learning to learn)."""
    timestamp: int
    problem_class: str
    strategy: str
    lenses_used: List[str]
    monte_carlo_n: int
    seed: int
    outcome: str          # PASS | FAIL | REFUTED_PRESERVED | UNDERDETERMINED
    time_to_decision_s: float
    predicted_probability: float
    observed_outcome_value: Optional[float] = None

    def calibration_error(self) -> float:
        if self.observed_outcome_value is None:
            return 0.0
        if self.outcome == "PASS":
            target = 1.0
        elif self.outcome in ("REFUTED_PRESERVED", "FAIL"):
            target = 0.0
        else:
            target = 0.5
        return abs(self.predicted_probability - target)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningRecord":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)
