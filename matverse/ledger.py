"""
matverse.ledger
===============

Hash-chained, append-only ledger. Each Receipt references the previous
ledger_hash, making any post-hoc tampering detectable.

The ledger is a proof of local integrity. It does NOT prove:
  - factual truth
  - external scientific validity
  - quality of the underlying decision

It DOES prove:
  - the order of recorded events
  - that the input/output hashes correspond to the recorded payload
  - that nothing in the chain was silently rewritten
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


GENESIS_HASH = "0" * 64


def _stable_hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


@dataclass
class Receipt:
    timestamp: int
    input_hash: str
    output_hash: str
    status: str
    ledger_prev: str
    ledger_hash: str
    kind: str = "generic"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        allowed = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


class Ledger:
    """Append-only, hash-chained ledger."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._entries: List[Receipt] = []
        self._last_hash: str = GENESIS_HASH
        self._path = path

    def __len__(self) -> int:
        return len(self._entries)

    def append(
        self,
        *,
        kind: str,
        input_obj: Any,
        output_obj: Any,
        status: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Receipt:
        ts = int(time.time())
        i_hash = _stable_hash(input_obj)
        o_hash = _stable_hash(output_obj)
        chain = f"{i_hash}{o_hash}{self._last_hash}{status}{kind}{ts}"
        new_hash = hashlib.sha256(chain.encode()).hexdigest()
        rec = Receipt(
            timestamp=ts,
            input_hash=i_hash,
            output_hash=o_hash,
            status=status,
            ledger_prev=self._last_hash,
            ledger_hash=new_hash,
            kind=kind,
            extra=extra or {},
        )
        self._entries.append(rec)
        self._last_hash = new_hash
        if self._path:
            self.flush()
        return rec

    def entries(self) -> List[Receipt]:
        return list(self._entries)

    def flush(self) -> None:
        if not self._path:
            return
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        if not self._path:
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            return
        self._entries = [Receipt.from_dict(r) for r in raw]
        if self._entries:
            self._last_hash = self._entries[-1].ledger_hash
        else:
            self._last_hash = GENESIS_HASH

    def verify(self) -> Dict[str, Any]:
        """Walk the chain and verify that each entry's ledger_hash matches the
        recomputed value. Returns a status dict."""
        prev = GENESIS_HASH
        for i, e in enumerate(self._entries):
            chain = f"{e.input_hash}{e.output_hash}{prev}{e.status}{e.kind}{e.timestamp}"
            expected = hashlib.sha256(chain.encode()).hexdigest()
            if expected != e.ledger_hash:
                return {"ok": False, "broken_at": i, "expected": expected, "got": e.ledger_hash}
            prev = e.ledger_hash
        return {"ok": True, "length": len(self._entries), "tip": self._last_hash}
