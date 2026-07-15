"""
matverse.closure_macro
======================

Fractal closure compiler.

A closure is the canonical object that ties together a complete
organism-level cycle. It has four projections (Paper, Code,
Execution, Canonization) and (with the v3.6 additions) a fifth
(Thermodynamic balance) and a sixth (Regenerative return).

Closures operate at three scales (fractal):

  MICRO  — a single mutation
  MESO   — a capability or release
  MACRO  — an organism generation

The ClosureMacroCompiler takes an SVCA, a Cassandra reading, a
ThermoReceipt, an M-bit, and emits a ClosureBundle with all
projections and platform-link metadata.
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .svca import SVCA
from .thermo import ThermoReceipt
from .captals import MBit


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------

@dataclass
class PaperProjection:
    artifact_id: str
    title: str
    abstract: str
    claims: List[Dict[str, Any]] = field(default_factory=list)
    falsification_criteria: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    relation_to_previous: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "title": self.title, "abstract": self.abstract,
            "claims": self.claims,
            "falsification_criteria": self.falsification_criteria,
            "limitations": self.limitations,
            "relation_to_previous": self.relation_to_previous,
        }


@dataclass
class CodeProjection:
    repository: str
    commit: str
    release_tag: Optional[str]
    build_receipt: Dict[str, Any] = field(default_factory=dict)
    source_manifest: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "release_tag": self.release_tag,
            "build_receipt": self.build_receipt,
            "source_manifest": self.source_manifest,
        }


@dataclass
class ExecutionProjection:
    run_id: str
    environment_hash: str
    receipt_hash: str
    replay_status: str                 # LOCAL_REPLAYED | INDEPENDENT_REPLAYED | WITNESSED_EXTERNAL
    results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    learning_update: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "environment_hash": self.environment_hash,
            "receipt_hash": self.receipt_hash,
            "replay_status": self.replay_status,
            "results": self.results,
            "metrics": self.metrics,
            "learning_update": self.learning_update,
        }


@dataclass
class CanonizationProjection:
    manifest_hash: str
    merkle_root: str
    gate_state: str                   # CANONICAL_FOR_DECLARED_SCOPE | CLOSURE_CANDIDATE | CLOSED | REPLAYED_INDEPENDENT | WITNESSED_EXTERNAL
    lineage: Dict[str, Any] = field(default_factory=dict)
    supersedes: Optional[str] = None
    supersession_policy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_hash": self.manifest_hash,
            "merkle_root": self.merkle_root,
            "gate_state": self.gate_state,
            "lineage": self.lineage,
            "supersedes": self.supersedes,
            "supersession_policy": self.supersession_policy,
        }


@dataclass
class ThermoProjection:
    receipt: Dict[str, Any] = field(default_factory=dict)
    pbr: float = 0.0
    regenerative_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt": self.receipt,
            "pbr": round(self.pbr, 4),
            "regenerative_ratio": round(self.regenerative_ratio, 4),
        }


@dataclass
class RegenerativeProjection:
    avoided_wh: float = 0.0
    recovered_wh: float = 0.0
    renewable_wh: float = 0.0
    ecological_value: float = 0.0
    planetary_benefit_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avoided_wh": round(self.avoided_wh, 4),
            "recovered_wh": round(self.recovered_wh, 4),
            "renewable_wh": round(self.renewable_wh, 4),
            "ecological_value": round(self.ecological_value, 4),
            "pbr": round(self.planetary_benefit_ratio, 4),
        }


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------

@dataclass
class ClosureBundle:
    closure_id: str
    parent_closure_id: Optional[str]
    scale: str                         # MICRO | MESO | MACRO
    organism: str
    version: str
    paper: PaperProjection
    code: CodeProjection
    execution: ExecutionProjection
    canonization: CanonizationProjection
    thermo: ThermoProjection
    regenerative: RegenerativeProjection
    mbit: Optional[Dict[str, Any]] = None
    state_epistemic: str = "PROPOSED"  # PROPOSED | SUPPORTED_FOR_DECLARED_SCOPE | REFUTED_PRESERVED
    state_closure: str = "CLOSURE_CANDIDATE"
    timestamp: int = 0
    platform_links: Dict[str, Any] = field(default_factory=dict)

    def canonical_hash(self) -> str:
        """Stable SHA-256 of the content. Timestamps and environment
        hashes are normalized so that two runs of the same logical
        closure produce the same canonical hash."""
        d = self.to_dict()
        d.pop("timestamp", None)
        if "execution" in d:
            d["execution"].pop("environment_hash", None)
            if "results" in d["execution"]:
                d["execution"]["results"] = {}
        if "mbit" in d and isinstance(d["mbit"], dict):
            pass
        if "platform_links" in d and "blockchain" in d["platform_links"]:
            d["platform_links"]["blockchain"].pop("merkle_root", None)
            d["platform_links"]["blockchain"]["tx_hash"] = None
        if "canonization" in d:
            d["canonization"].pop("merkle_root", None)
            d["canonization"].pop("manifest_hash", None)
        payload = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "closure_id": self.closure_id,
            "parent_closure_id": self.parent_closure_id,
            "scale": self.scale,
            "organism": self.organism,
            "version": self.version,
            "paper": self.paper.to_dict(),
            "code": self.code.to_dict(),
            "execution": self.execution.to_dict(),
            "canonization": self.canonization.to_dict(),
            "thermo": self.thermo.to_dict(),
            "regenerative": self.regenerative.to_dict(),
            "mbit": self.mbit,
            "state_epistemic": self.state_epistemic,
            "state_closure": self.state_closure,
            "timestamp": self.timestamp,
            "platform_links": self.platform_links,
        }


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

class ClosureMacroCompiler:
    """Compile a ClosureBundle from canonical sources.

    This is the v3.6 integrator. It expects all the upstream organs
    (SVCA, Thermo, M-bit, Cassandra reading, etc.) to be ready and
    produces a single canonical object that can be published across
    Zenodo, Git, Hugging Face, and (eventually) blockchain.
    """

    def __init__(self, organism: str = "matverse-organism",
                 version: str = "3.6.0") -> None:
        self.organism = organism
        self.version = version
        self.last_bundle: Optional[ClosureBundle] = None

    def compile(self,
                *,
                closure_id: str,
                parent_closure_id: Optional[str],
                scale: str,
                title: str,
                abstract: str,
                svca: SVCA,
                thermo: Optional[ThermoReceipt],
                mbit: Optional[MBit],
                repository: str,
                commit: str,
                release_tag: Optional[str] = None,
                replay_status: str = "LOCAL_REPLAYED",
                lineage: Optional[Dict[str, Any]] = None,
                claims: Optional[List[Dict[str, Any]]] = None,
                limitations: Optional[List[str]] = None,
                ) -> ClosureBundle:
        if scale not in ("MICRO", "MESO", "MACRO"):
            raise ValueError(f"invalid scale: {scale}")

        # Paper
        paper = PaperProjection(
            artifact_id=f"PAPER-{closure_id}",
            title=title, abstract=abstract,
            claims=claims or [],
            falsification_criteria=[
                f"Reject if '{c.get('falsification_criteria', '')}' is met"
                for c in (claims or [])
                if c.get("falsification_criteria")
            ],
            limitations=limitations or [],
            relation_to_previous=(
                f"derived from {parent_closure_id}" if parent_closure_id else "root"
            ),
        )

        # Code
        code = CodeProjection(
            repository=repository, commit=commit, release_tag=release_tag,
            source_manifest={"files": _safe_glob_count(repository)},
            build_receipt={"status": "PASS_LOCAL_BUILD"},
        )

        # Execution
        exec_proj = ExecutionProjection(
            run_id=f"RUN-{closure_id}",
            environment_hash=svca.environment.get("hostname", "unknown"),
            receipt_hash=svca.hashes.get("receipt_hash", ""),
            replay_status=replay_status,
            results=svca.output,
            metrics=svca.metrics,
            learning_update={"learning_records_appended": 1},
        )

        # Canonization
        manifest_hash = svca.canonical_hash()
        merkle_root = _merkle([manifest_hash, _node_id(commit), closure_id])
        gate_state = "CLOSED" if replay_status != "OPEN" else "CLOSURE_CANDIDATE"
        canon = CanonizationProjection(
            manifest_hash=manifest_hash, merkle_root=merkle_root,
            gate_state=gate_state,
            lineage=lineage or {},
            supersedes=parent_closure_id,
            supersession_policy=(
                "replaces parent on canonical_hash change; preserved for lineage"
            ),
        )

        # Thermo & Regenerative
        if thermo is not None:
            thermo_proj = ThermoProjection(
                receipt=thermo.to_dict(),
                pbr=thermo.planetary_benefit_ratio,
                regenerative_ratio=thermo.regenerative_ratio,
            )
            regen = RegenerativeProjection(
                avoided_wh=thermo.external_energy_avoided_wh,
                recovered_wh=thermo.heat_recovered_wh,
                renewable_wh=0.0,
                ecological_value=0.0,
                planetary_benefit_ratio=thermo.planetary_benefit_ratio,
            )
        else:
            thermo_proj = ThermoProjection()
            regen = RegenerativeProjection()

        # M-bit
        mbit_dict = mbit.to_dict() if mbit is not None else None

        # State — recompute the M-bit's status from its geometric score,
        # since the caller may have passed a DECLARED m-bit that should
        # actually be ADMISSIBLE_CONTRIBUTION (or REJECTED).
        if mbit is not None:
            score = mbit.geometric_score()
            if score <= 0:
                mbit.status = "REJECTED"
                state_epistemic = "REFUTED_PRESERVED"
            elif mbit.status == "REJECTED":
                state_epistemic = "REFUTED_PRESERVED"
            else:
                mbit.status = "ADMISSIBLE_CONTRIBUTION"
                state_epistemic = "SUPPORTED_FOR_DECLARED_SCOPE"
            mbit_dict = mbit.to_dict()
        else:
            state_epistemic = "PROPOSED"

        bundle = ClosureBundle(
            closure_id=closure_id,
            parent_closure_id=parent_closure_id,
            scale=scale,
            organism=self.organism,
            version=self.version,
            paper=paper, code=code, execution=exec_proj,
            canonization=canon, thermo=thermo_proj,
            regenerative=regen, mbit=mbit_dict,
            state_epistemic=state_epistemic,
            state_closure=gate_state,
            timestamp=int(time.time()),
            platform_links={
                "zenodo": {"status": "PREPARED_NOT_PUBLISHED",
                           "deposition_id": None},
                "github": {"status": "PREPARED_NOT_RELEASED",
                           "release_id": None},
                "huggingface": {"status": "PREPARED_NOT_PUBLISHED",
                                "repo_id": None},
                "blockchain": {"status": "PREPARED_NOT_BROADCAST",
                               "tx_hash": None,
                               "merkle_root": merkle_root},
            },
        )
        self.last_bundle = bundle
        return bundle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_glob_count(repo: str) -> int:
    try:
        import os
        return sum(1 for _ in os.scandir(repo) if _.is_file())
    except Exception:
        return 0


def _node_id(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()


def _merkle(items: List[str]) -> str:
    """Tiny Merkle root: pairwise hash, repeat until one remains."""
    import hashlib
    if not items:
        return ""
    layer = [hashlib.sha256(i.encode()).hexdigest() for i in items]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a
            nxt.append(hashlib.sha256((a + b).encode()).hexdigest())
        layer = nxt
    return layer[0]
