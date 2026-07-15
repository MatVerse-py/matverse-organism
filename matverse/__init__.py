"""
matverse-organism v3.6.0
========================

The integrative cognitive layer of the MatVerse ecosystem.

v3.6.0 is the eight-organs-plus-one release: it wires together the
canonical anatomy defined in the corpus, including:

  - Campo de Hipóteses (Hypothesis Field)
  - URANO / UMJAM (Hypothesis -> Experiment -> Transmutation)
  - Closure Compiler (v3.0) + Closure Macro Compiler (v3.6)
  - Metacortex (level-3 learning: learning to learn)
  - 8 Constitutional Laws (versioned operational policies)
  - 8 Invariants (fail-closed constitutional conditions)
  - AXIS-8 analytical lenses
  - Hash-chained, append-only ledger
  - Monte Carlo with CVaR and local sensitivity
  - Cassandra (cognitive interpretation layer)
  - SVCA (proof capsule)
  - Atlas (live cartographic projection)
  - ThermoCortex (thermodynamic accounting + PBR)
  - Captals + M-bit + Proof Chain (continuity allocator)
  - Existential organs: Metabolism, Autopoiesis, Apoptosis,
    Antifragility, Homeostasis
  - Publication layer: Zenodo, GitHub Release, Hugging Face, Blockchain
  - Replayer (independent replay verification)
  - FullOrganismRunner (the canonical wiring of all organs)

Public API:
    from matverse import FullOrganismRunner, Organism, Problem, Hypothesis
    from matverse import Invariants, Cassandra, UMJAM, SVCA, Atlas
    from matverse import ThermoCortex, CaptalsEngine, ClosureMacroCompiler
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

__version__ = "3.7.0"
__sha256_seed__ = "v3.7-seed-2026-07-14"

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
]
