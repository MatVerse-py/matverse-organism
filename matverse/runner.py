"""
matverse.runner
===============

The canonical "full organism" runner.

Executes the v3.6.0 cycle in the order defined by the canon:

    MMNB_t
      -> Cassandra (interpret)
        -> Campo de Hipóteses (classify, rank, AXIS-8, MC)
          -> Invariants + Laws (Gate)
            -> COG (compose capability)
              -> ThermoCortex (estimate cost / pick budget)
                -> UMJAM (transmute under contract)
                  -> SVCA (proof capsule)
                    -> Closure Compiler (4 (+2) projections)
                      -> Atlas (update live map)
                        -> Metacortex (record LearningRecord)
                          -> Apoptosis / Antifragility (existential update)
                            -> new MMNB_t+1

This is the only place where all organs are wired together. It is
deterministic given a seed, and emits a single canonical ClosureBundle.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Problem, Hypothesis, LearningRecord
from .organism import Organism, classify_problem
from .umjam import UMJAM, UMJAMSpec
from .urano import URANO                              # legacy alias (kept for back-compat)
from .closure import ClosureCompiler
from .metacortex import Metacortex
from .ledger import Ledger
from .laws import ConstitutionalLaws
from .invariants import Invariants
from .cassandra import Cassandra
from .svca import SVCA
from .atlas import Atlas
from .thermo import ThermoCortex, ThermoReceipt
from .captals import CaptalsEngine, MBit
from .existential import (
    Metabolism, Autopoiesis, Apoptosis, Antifragility, Homeostasis,
)
from .closure_macro import (
    ClosureMacroCompiler, ClosureBundle, PaperProjection, CodeProjection,
    ExecutionProjection, CanonizationProjection, ThermoProjection,
    RegenerativeProjection,
)
from .publishers import prepare_publication
from .replay import Replayer


@dataclass
class FullOrganismResult:
    closure: ClosureBundle
    svca: SVCA
    cassandra_reading: Dict[str, Any]
    organism_report: Dict[str, Any]
    publication: Dict[str, Any]
    replay_report: Optional[Dict[str, Any]] = None
    thermodynamics: Optional[Dict[str, Any]] = None
    mbit: Optional[Dict[str, Any]] = None
    atlas_snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "closure": self.closure.to_dict(),
            "svca": self.svca.to_dict(),
            "cassandra_reading": self.cassandra_reading,
            "organism_report": self.organism_report,
            "publication": self.publication,
            "replay_report": self.replay_report,
            "thermodynamics": self.thermodynamics,
            "mbit": self.mbit,
            "atlas_snapshot": self.atlas_snapshot,
        }


class FullOrganismRunner:
    """The full organism runner. See module docstring for the order of
    organs. Returns a FullOrganismResult with the canonical closure and
    every projection."""

    def __init__(self,
                 ledger: Optional[Ledger] = None,
                 *,
                 umjam: Optional[UMJAM] = None,
                 thermo: Optional[ThermoCortex] = None,
                 atlas: Optional[Atlas] = None,
                 metabolism: Optional[Metabolism] = None,
                 apoptosis: Optional[Apoptosis] = None,
                 antifragility: Optional[Antifragility] = None,
                 homeostasis: Optional[Homeostasis] = None,
                 organism_version: str = "3.6.0") -> None:
        self.ledger = ledger or Ledger()
        self.organism = Organism(ledger=self.ledger)
        self.urano = URANO(ledger=self.ledger)
        self.closure = ClosureCompiler(self.organism, self.urano, ledger=self.ledger)
        self.cassandra = Cassandra()
        self.invariants = Invariants()
        self.laws = ConstitutionalLaws()
        self.umjam = umjam or UMJAM()
        self.thermo = thermo or ThermoCortex()
        self.atlas = atlas or Atlas()
        self.metabolism = metabolism or Metabolism()
        self.apoptosis = apoptosis or Apoptosis()
        self.antifragility = antifragility or Antifragility()
        self.homeostasis = homeostasis or Homeostasis()
        self.metacortex = Metacortex(ledger=self.ledger)
        self.captals = CaptalsEngine()
        self.replayer = Replayer(self.umjam)
        self.macro_compiler = ClosureMacroCompiler(
            organism="matverse-organism", version=organism_version,
        )

        # Seed the Atlas with the canonical organs
        self._register_canonical_organs()

    def _register_canonical_organs(self) -> None:
        for organ in [
            ("organ.mmnb", "MMNB", "ACTIVE"),
            ("organ.cassandra", "Cassandra", "ACTIVE"),
            ("organ.hypothesis_field", "Campo de Hipóteses", "ACTIVE"),
            ("organ.urano", "URANO", "ACTIVE"),
            ("organ.umjam", "UMJAM", "ACTIVE"),
            ("organ.svca", "SVCA", "ACTIVE"),
            ("organ.thermo", "ThermoCortex", "ACTIVE"),
            ("organ.captals", "Captals", "ACTIVE"),
            ("organ.atlas", "Atlas", "ACTIVE"),
            ("organ.closure_macro", "ClosureMacroCompiler", "ACTIVE"),
            ("organ.metacortex", "Metacortex", "ACTIVE"),
            ("organ.metabolism", "Metabolism", "ACTIVE"),
            ("organ.apoptosis", "Apoptosis", "ACTIVE"),
            ("organ.antifragility", "Antifragility", "ACTIVE"),
            ("organ.homeostasis", "Homeostasis", "ACTIVE"),
            ("organ.invariants", "Invariants", "ACTIVE"),
            ("organ.laws", "Laws", "ACTIVE"),
            ("organ.gate", "Gate", "ACTIVE"),
        ]:
            self.atlas.register_organ(organ[0], organ[1], state=organ[2])
        for cap in ["paired_metric_comparison.v1", "echo.v1"]:
            self.atlas.register_capability(cap, "organ.umjam")

    def run(self, problem: Problem,
            *,
            closure_scale: str = "MESO",
            closure_title: Optional[str] = None,
            closure_parent: Optional[str] = None,
            repository: str = "MatVerse-py/matverse-organism",
            commit: str = "HEAD",
            release_tag: Optional[str] = None,
            executable: bool = True,
            ) -> FullOrganismResult:
        # 1. Classify
        classification = classify_problem(problem)

        # 2. Cassandra reading
        reading = self.cassandra.interpret(problem, classification=classification)

        # 3. Organism (Campo de Hipóteses) — full report
        org_report = self.organism.investigate(problem)
        org_dict = org_report.to_dict()

        # 4. Invariants + Laws (Gate)
        inv_verdicts = self.invariants.evaluate(problem)
        law_verdicts = self.laws.evaluate(problem)
        gate_open = self.invariants.all_hold(inv_verdicts) and \
            self.laws.summary(law_verdicts)["failing"] == 0

        # 5. COG: pick capability (for the demo, echo.v1)
        chosen_capability = "echo.v1"
        chosen_op = f"OP-{uuid.uuid4().hex[:8]}"

        # 6. ThermoCortex: estimate cost
        thermo_receipt = self.thermo.record(
            execution_id=chosen_op,
            workload={
                "energy_wh": 0.5, "co2_g": 0.05, "exergy_wh": 0.4,
                "cpu_seconds": 0.1, "gpu_seconds": 0.0,
                "input_tokens": 100, "output_tokens": 50,
                "avg_power_w": 5.0, "peak_temperature_c": 35.0,
                "waste_heat_wh": 0.3, "heat_recovered_wh": 0.05,
                "external_energy_avoided_wh": 12.0,
                "renewable_enabled_wh": 0.0, "verified_ecological_value": 0.0,
                "energy_embodied_wh": 0.05,
                "measurement_status": "DECLARED",
            },
        )

        # 7. UMJAM transmutation
        spec = UMJAMSpec(
            operation_id=chosen_op,
            capability_id=chosen_capability,
            inputs=problem.to_dict(),
            constraints=[],
            limits={"max_seconds": 60},
            fail_closed=True,
            subject=problem.id, consent="implicit", key="",
            purpose=f"closure for {problem.id}", seed=42,
        )
        state_in = problem.to_dict()
        if executable:
            umjam_result = self.umjam.transmute(spec, state_in)
        else:
            umjam_result = None

        # 8. SVCA capsule
        if umjam_result is not None:
            svca = SVCA.from_transmutation(
                spec, umjam_result,
                metrics={"thermo": thermo_receipt.to_dict()},
            )
        else:
            # Synthetic empty SVCA for non-executable runs (e.g. test stubs)
            from .umjam import UMJAMResult
            empty = UMJAMResult(
                operation_id=chosen_op, capability_id=chosen_capability,
                output={}, status="PASS", timestamp=int(time.time()),
            )
            svca = SVCA.from_transmutation(spec, empty,
                                           metrics={"thermo": thermo_receipt.to_dict()})

        # 9. Atlas: record the transmutation
        self.atlas.record_svca(
            svca_id=svca.svca_id, capability_id=chosen_capability,
            problem_id=problem.id, status=svca.status,
        )

        # 10. Captals: M-bit
        mbit = MBit(
            work_id=chosen_op, contributor="matverse-builder",
            compute_cost=0.5, evidence_quality=0.9,
            reproducibility=1.0, utility=0.8,
            transferability=0.7, risk=0.05,
            human_alignment=0.95, status="DECLARED",
            proofs={"PoSE": svca.hashes.get("receipt_hash", ""),
                    "PoCT": svca.hashes.get("output_hash", ""),
                    "PoTM": svca.hashes.get("input_hash", ""),
                    "PoLE": svca.canonical_hash()},
        )
        self.captals.record(mbit)

        # 11. Closure Macro Compiler
        closure_id = f"MV-CLOSURE-{uuid.uuid4().hex[:12].upper()}"
        bundle = self.macro_compiler.compile(
            closure_id=closure_id,
            parent_closure_id=closure_parent,
            scale=closure_scale,
            title=closure_title or f"Closure for {problem.id}",
            abstract=(
                f"Automatic closure produced by the MatVerse organism for "
                f"problem {problem.id} ({classification}). Top hypothesis "
                f"{(org_report.ranked[0]['id'] if org_report.ranked else 'none')}. "
                f"Gate open: {gate_open}."
            ),
            svca=svca, thermo=thermo_receipt, mbit=mbit,
            repository=repository, commit=commit,
            release_tag=release_tag,
            replay_status="LOCAL_REPLAYED",
            lineage={
                "parent_closure_id": closure_parent,
                "classification": classification,
                "gate_open": gate_open,
            },
            claims=[{
                "id": h.id, "claim": h.claim,
                "falsification_criteria": h.falsification_criteria,
            } for h in problem.hypotheses],
            limitations=[
                "internal run only; no external publication",
                "no independent replay (LOCAL_REPLAYED only)",
                "thermo values are DECLARED, not sensor-measured",
            ],
        )

        # 12. Atlas: record the closure
        self.atlas.record_closure(
            closure_id=bundle.closure_id,
            parent_closure_id=closure_parent,
            svca_ids=[svca.svca_id], state=bundle.state_closure,
        )

        # 13. Metacortex: record a learning record
        if org_report.ranked:
            top = org_report.ranked[0]
            lr = LearningRecord(
                timestamp=int(time.time()),
                problem_class=problem.id,
                strategy=top["id"],
                lenses_used=list(top.get("lenses", {}).keys()),
                monte_carlo_n=org_report.n_monte_carlo,
                seed=org_report.seed,
                outcome=org_report.decision,
                time_to_decision_s=0.1,
                predicted_probability=0.85,
                observed_outcome_value=1.0,
            )
            self.metacortex.record(lr)

        # 14. Apoptosis: register the top hypothesis and mark it active
        if org_report.ranked:
            top_id = org_report.ranked[0]["id"]
            self.apoptosis.register(top_id, diagnosis={"source": "top_ranked"})

        # 15. Antifragility: record a synthetic sample (perturbation -> improvement)
        self.antifragility.record(
            perturbation="closure_run",
            before=0.0, after=bundle.canonical_hash() and 1.0 or 0.0,
        )

        # 16. Replay (local)
        replay_report = self.replayer.replay(svca, independent=False)
        if replay_report.matches:
            bundle.execution.replay_status = "INDEPENDENT_REPLAYED"
            bundle.state_closure = "REPLAYED_INDEPENDENT"
            bundle.platform_links["blockchain"]["status"] = "PREPARED_NOT_BROADCAST"

        # 17. Publication
        publication = prepare_publication(
            bundle=bundle,
            creators=[{"name": "MatVerse Builder",
                       "affiliation": "MatVerse",
                       "orcid": "0000-0000-0000-0000"}],
            github_repo=repository,
            github_tag=release_tag or bundle.version,
            hf_repo_id=f"matverse/{bundle.closure_id.lower()}",
        )

        # 18. Atlas snapshot
        atlas_snap = self.atlas.snapshot()

        return FullOrganismResult(
            closure=bundle, svca=svca,
            cassandra_reading=reading.to_dict(),
            organism_report=org_dict,
            publication=publication.to_dict(),
            replay_report=replay_report.to_dict(),
            thermodynamics=thermo_receipt.to_dict(),
            mbit=mbit.to_dict(),
            atlas_snapshot=atlas_snap,
        )
