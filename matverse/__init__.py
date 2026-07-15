"""
matverse-organism v3.8.0
========================

The integrative cognitive layer of the MatVerse ecosystem.

v3.8.0 — "GTHDL integration": closes the canonical gaps that the corpus
identifies but v3.7.0 left open.

The organism has 12 constitutional organs (v3.8.0) organized in a single
cycle, plus 3 constitutional-physics objects (NEW in v3.8.0):

  Constitutional organs (12):
    1.  MMNB                    — causal memory (seed of the next cycle)
    2.  Cassandra / MetaCortex  — cognitive interpretation + L3 learning
    3.  COG (Campo de Hipóteses) — hypothesis field
    4.  Invariants              — fail-closed constitutional gate
    5.  Laws                    — versioned operational policies
    6.  UMJAM                   — admissible mutation
    7.  SVCA                    — proof capsule
    8.  Closure                 — closure compiler (v3.0 + v3.6 macro)
    9.  Atlas                   — live cartographic projection
    10. Thermodynamic Cortex    — energy / PBR / regenerative accounting
    11. Captals                 — continuity allocator + M-bit
    12. Existential Processes   — metabolism, autopoiesis, apoptosis,
                                  antifragility, homeostasis

  Constitutional physics (3, NEW in v3.8.0):
    - GTHDL Hamiltonian        — dρ/dt = -i [Ĥ_Σ, ρ] (matverse.hamiltonian)
    - Riemannian Memory Manifold — M = (O, R, g, Φ, ρ) (matverse.riemannian)
    - Epistemic State Machine   — 8 states + Dempster-Shafer + Dung
                                  (matverse.epistemic)

  Constitutional object (v3.8.0):
    - Formal MNB (5-tuple)     — m = (e, Ψ, C, τ, h), ρ = Ψ·τ/C
                                  (matverse.mnb_formal)
    - Omega Score Ω             — normalized 5-dim geometric mean
                                  (matverse.omega)
    - 12-organism taxonomy      — (matverse.canonical)

Public API:
    from matverse import FullOrganismRunner, Organism, Problem, Hypothesis
    from matverse import Invariants, Cassandra, UMJAM, SVCA, Atlas
    from matverse import ThermoCortex, CaptalsEngine, ClosureMacroCompiler
    from matverse import FormalMNB, Hamiltonian, DensityOperator, GTHDLPropagator
    from matverse import RiemannianMemoryManifold, EpistemicState,
                            dempster_combine, dung_preferred_extensions
    from matverse import omega_score, omega_from_closure,
                            CONSTITUTIONAL_ORGANS_V3_8
"""
from .organism import Organism, Problem, Hypothesis, HypothesisStatus
from .urano import URANO, ExperimentContract, ExperimentResult
from .umjam import UMJAM, UMJAMSpec, UMJAMResult, CapabilityRegistry
from .closure import ClosureCompiler, ClosureReport
from .metacortex import Metacortex, LearningRecord
from .ledger import Ledger, Receipt
from .laws import ConstitutionalLaws, LawVerdict
from .invariants import Invariants, InvariantVerdict, InvariantViolation
from .axis8 import AXIS8
from .monte_carlo import monte_carlo, cvar, sensitivity
from .cassandra import Cassandra, CassandraReading
from .svca import SVCA
from .atlas import Atlas, AtlasNode, AtlasEdge
from .thermo import (
    ThermoCortex, ThermoReceipt, Probe, DeclaredProbe,
    exergy, planetary_benefit_ratio,
)
from .captals import (
    CaptalsEngine, MBit, ProofChain, WorkContract, LCUAccount,
)
from .existential import (
    Metabolism, MetabolismBudget, Autopoiesis, Apoptosis,
    Antifragility, Homeostasis, APOPTOSIS_STATES,
)
from .closure_macro import (
    ClosureMacroCompiler, ClosureBundle, PaperProjection, CodeProjection,
    ExecutionProjection, CanonizationProjection, ThermoProjection,
    RegenerativeProjection,
)
from .publishers import (
    prepare_publication, PublicationSet, zenodo_metadata,
    github_release_metadata, huggingface_metadata, blockchain_anchor,
)
from .replay import Replayer, ReplayReport
from .runner import FullOrganismRunner, FullOrganismResult
from .capability import CapabilityRegistry as CanonicalCapabilityRegistry, CapabilityContract
from .mmnb import MMNB, MMNBStore
from .adaptation import (
    AdaptationMetacortex, ApoptosisScheduler, AutopoiesisGenerator,
    CrossRunOrganism, CapabilityGap,
)
from .probes import (
    DeclaredProbe as ProbeDeclared, RaplProbe, NvmlProbe,
    CompositeProbe, make_default_probe, ProbeMeasurement,
)
# v3.8.0 — constitutional physics and objects
from .mnb_formal import (
    FormalMNB, MNBState, MNBPhase, ThermodynamicGate, prune, from_payload,
)
from .hamiltonian import (
    Hamiltonian, HamiltonianOperators, DensityOperator,
    GTHDLPropagator, commutator, evolve_rho, check_conservation,
)
from .riemannian import (
    MetricTensor, CurvatureTensor, RiemannianMemoryManifold,
    adjusted_cost_manifold,
)
from .epistemic import (
    EpistemicState, EpistemicPolicy, SourceMetadata, Evidence,
    BeliefRecord, dempster_combine, irc, dung_preferred_extensions,
    attack_graph, evaluate_gate, GateDecision,
)
from .omega import (
    omega_score, omega_from_closure, interpret_omega,
    normalize_pbr, normalize_rrec, OmegaReport,
)
from .canonical import (
    CONSTITUTIONAL_ORGANS_V3_8, CONSTITUTIONAL_PHYSICS_V3_8,
    ConstitutionalState, next_organ,
)

__version__ = "3.8.1"
__sha256_seed__ = "v3.8-seed-2026-07-15"

__all__ = [
    # v3.0
    "Organism", "Problem", "Hypothesis", "HypothesisStatus",
    "URANO", "ExperimentContract", "ExperimentResult",
    "ClosureCompiler", "ClosureReport",
    "Metacortex", "LearningRecord",
    "Ledger", "Receipt",
    "ConstitutionalLaws", "LawVerdict",
    "AXIS8", "monte_carlo", "cvar", "sensitivity",
    # v3.1
    "Invariants", "InvariantVerdict", "InvariantViolation",
    "Cassandra", "CassandraReading",
    "UMJAM", "UMJAMSpec", "UMJAMResult", "CapabilityRegistry",
    # v3.2
    "SVCA", "Atlas", "AtlasNode", "AtlasEdge",
    # v3.3
    "Metabolism", "MetabolismBudget", "Autopoiesis", "Apoptosis",
    "Antifragility", "Homeostasis", "APOPTOSIS_STATES",
    # v3.4
    "ThermoCortex", "ThermoReceipt", "Probe", "DeclaredProbe",
    "exergy", "planetary_benefit_ratio",
    # v3.5
    "CaptalsEngine", "MBit", "ProofChain", "WorkContract", "LCUAccount",
    # v3.6
    "ClosureMacroCompiler", "ClosureBundle", "PaperProjection",
    "CodeProjection", "ExecutionProjection", "CanonizationProjection",
    "ThermoProjection", "RegenerativeProjection",
    "prepare_publication", "PublicationSet", "zenodo_metadata",
    "github_release_metadata", "huggingface_metadata", "blockchain_anchor",
    "Replayer", "ReplayReport",
    "FullOrganismRunner", "FullOrganismResult",
    "CanonicalCapabilityRegistry", "CapabilityContract",
    "MMNB", "MMNBStore",
    "AdaptationMetacortex", "ApoptosisScheduler", "AutopoiesisGenerator",
    "CrossRunOrganism", "CapabilityGap",
    "ProbeDeclared", "RaplProbe", "NvmlProbe", "CompositeProbe",
    "make_default_probe", "ProbeMeasurement",
    # v3.8.0 — constitutional physics and objects
    "FormalMNB", "MNBState", "MNBPhase", "ThermodynamicGate", "prune",
    "from_payload",
    "Hamiltonian", "HamiltonianOperators", "DensityOperator",
    "GTHDLPropagator", "commutator", "evolve_rho", "check_conservation",
    "MetricTensor", "CurvatureTensor", "RiemannianMemoryManifold",
    "adjusted_cost_manifold",
    "EpistemicState", "EpistemicPolicy", "SourceMetadata", "Evidence",
    "BeliefRecord", "dempster_combine", "irc", "dung_preferred_extensions",
    "attack_graph", "evaluate_gate", "GateDecision",
    "omega_score", "omega_from_closure", "interpret_omega",
    "normalize_pbr", "normalize_rrec", "OmegaReport",
    "CONSTITUTIONAL_ORGANS_V3_8", "CONSTITUTIONAL_PHYSICS_V3_8",
    "ConstitutionalState", "next_organ",
]
