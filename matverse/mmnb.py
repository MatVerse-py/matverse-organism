"""
matverse.mmnb
==============

MMNB — Mem-Nano-Bit. The first-class causal memory object of the
organism. Every run of the organism reads a parent MMNB, applies the
delta of its own closure, and writes a child MMNB whose lineage
points back to the parent.

The MMNB is the only object in the organism that the operator should
NEVER delete. It is the seed of the next cycle.

Schema (deterministic, JSON-serializable):
  - id
  - parent_id (None for genesis)
  - lineage (list of MMNB ids from genesis to parent)
  - generation (0 for genesis, N for N-th descendant)
  - capabilities (list of capability ids active at this point)
  - recent_closures (list of closure ids in this lineage)
  - last_decision (the most recent OrganismReport.decision)
  - top_strategy (the most recent Metacortex.recommend result)
  - self_health (a snapshot of the existential organs at write time)
  - issued_at, issued_by
  - hash (canonical, computed at write time)
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


GENESIS_MMNB_ID = "MMNB-GENESIS-0000"


def _stable_hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


@dataclass
class MMNB:
    id: str
    parent_id: Optional[str]
    lineage: List[str] = field(default_factory=list)
    generation: int = 0
    capabilities: List[str] = field(default_factory=list)
    recent_closures: List[str] = field(default_factory=list)
    last_decision: str = ""
    top_strategy: str = ""
    self_health: Dict[str, Any] = field(default_factory=dict)
    issued_at: int = 0
    issued_by: str = ""
    notes: str = ""
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "parent_id": self.parent_id,
            "lineage": list(self.lineage), "generation": self.generation,
            "capabilities": list(self.capabilities),
            "recent_closures": list(self.recent_closures),
            "last_decision": self.last_decision,
            "top_strategy": self.top_strategy,
            "self_health": dict(self.self_health),
            "issued_at": self.issued_at, "issued_by": self.issued_by,
            "notes": self.notes, "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MMNB":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)

    def fingerprint(self) -> str:
        """Recompute the hash from the content (excluding the `hash` field)."""
        d = self.to_dict()
        d.pop("hash", None)
        return _stable_hash(d)

    def verify(self) -> bool:
        return self.fingerprint() == self.hash


# ---------------------------------------------------------------------------
# MMNB Store (persistent across runs)
# ---------------------------------------------------------------------------

class MMNBStore:
    """File-backed MMNB lineage store.

    Each MMNB is one JSON file in `directory`. The store indexes them
    by id and by generation. Loading a "current" MMNB means reading the
    most-recent one.
    """

    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self._index: Dict[str, MMNB] = {}
        self._load_all()

    def _load_all(self) -> None:
        self._index.clear()
        for name in sorted(os.listdir(self.directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.directory, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                mmnb = MMNB.from_dict(data)
                if mmnb.verify():
                    self._index[mmnb.id] = mmnb
            except Exception:
                continue

    def genesis(self, *, capabilities: Optional[List[str]] = None,
                issued_by: str = "matverse-organism") -> MMNB:
        """Create the genesis MMNB if no MMNB exists yet."""
        if self._index:
            return self.current()
        return self.write_new(
            parent_id=None, capabilities=capabilities or [],
            issued_by=issued_by,
            notes="genesis mmnb",
        )

    def current(self) -> Optional[MMNB]:
        if not self._index:
            return None
        return max(self._index.values(), key=lambda m: m.issued_at)

    def get(self, mmnb_id: str) -> Optional[MMNB]:
        return self._index.get(mmnb_id)

    def write_new(self, *,
                  parent: Optional[MMNB] = None,
                  parent_id: Optional[str] = None,
                  capabilities: Optional[List[str]] = None,
                  recent_closures: Optional[List[str]] = None,
                  last_decision: str = "",
                  top_strategy: str = "",
                  self_health: Optional[Dict[str, Any]] = None,
                  issued_by: str = "matverse-organism",
                  notes: str = "",
                  ) -> MMNB:
        if parent_id is None and parent is not None:
            parent_id = parent.id
        if parent is None and parent_id:
            parent = self._index.get(parent_id)
        lineage = list(parent.lineage) if parent else []
        if parent is not None:
            lineage.append(parent.id)
        generation = (parent.generation + 1) if parent else 0
        # Generate a unique id: use microsecond resolution + generation
        # + a counter to guarantee uniqueness even within the same
        # microsecond.
        ts = time.time()
        ts_us = int(ts * 1_000_000)
        # Counter: increment until the id is unique
        i = 0
        while True:
            mmnb_id = f"MMNB-{generation:04d}-{ts_us:x}-{i:x}"
            if mmnb_id not in self._index:
                break
            i += 1
        mmnb = MMNB(
            id=mmnb_id,
            parent_id=parent_id,
            lineage=lineage,
            generation=generation,
            capabilities=list(capabilities or []),
            recent_closures=list(recent_closures or []),
            last_decision=last_decision,
            top_strategy=top_strategy,
            self_health=dict(self_health or {}),
            issued_at=ts_us,
            issued_by=issued_by,
            notes=notes,
            hash="",
        )
        mmnb.hash = mmnb.fingerprint()
        self._save(mmnb)
        self._index[mmnb.id] = mmnb
        return mmnb

    def _save(self, mmnb: MMNB) -> None:
        path = os.path.join(self.directory, f"{mmnb.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mmnb.to_dict(), f, indent=2, ensure_ascii=False)

    def all(self) -> List[MMNB]:
        return sorted(self._index.values(), key=lambda m: m.issued_at)

    def summary(self) -> Dict[str, Any]:
        all_m = self.all()
        return {
            "directory": self.directory,
            "n_mmnbs": len(all_m),
            "current_id": all_m[-1].id if all_m else None,
            "current_generation": all_m[-1].generation if all_m else None,
            "current_capabilities": all_m[-1].capabilities if all_m else [],
        }
