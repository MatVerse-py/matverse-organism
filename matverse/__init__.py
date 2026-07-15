"""
matverse-organism v3.0.0
========================

The integrative cognitive layer of the MatVerse ecosystem.

This package provides:
  - Campo de Hipóteses (Hypothesis Field)
  - URANO Metabolic Runtime (Hypothesis -> Experiment)
  - Closure Compiler (cycle closure verifier)
  - Metacortex (level-3 learning: learning to learn)
  - 8 Constitutional Laws (lineage, gates, fail-closed)
  - AXIS-8 analytical lenses
  - Hash-chained, append-only ledger
  - Monte Carlo with CVaR and local sensitivity

Public API:
    from matverse import Organism, Hypothesis, Experiment, Metacortex
"""
from .organism import Organism, Problem, Hypothesis, HypothesisStatus
from .urano import URANO, ExperimentContract, ExperimentResult
from .closure import ClosureCompiler, ClosureReport
from .metacortex import Metacortex, LearningRecord
from .ledger import Ledger, Receipt
from .laws import ConstitutionalLaws, LawVerdict
from .axis8 import AXIS8
from .monte_carlo import monte_carlo, cvar, sensitivity

__version__ = "3.0.0"
__sha256_seed__ = "v3-seed-2026-07-14"

__all__ = [
    "Organism", "Problem", "Hypothesis", "HypothesisStatus",
    "URANO", "ExperimentContract", "ExperimentResult",
    "ClosureCompiler", "ClosureReport",
    "Metacortex", "LearningRecord",
    "Ledger", "Receipt",
    "ConstitutionalLaws", "LawVerdict",
    "AXIS8",
    "monte_carlo", "cvar", "sensitivity",
]
