"""
matverse.seeds
==============

MMNB (Mem-Nano-Bit) seed helpers. A seed encodes a deterministic starting
state for the organism (initial cells, hypotheses, capability registry, etc.).
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List


SEED_V3_2026_07_14 = {
    "id": "MMNB-v3-2026-07-14",
    "name": "matverse-organism-v3",
    "issued_at": 1721000000,
    "issued_by": "MatVerse Builder",
    "epoch": 3,
    "initial_cells": 686,
    "initial_capabilities": [
        "parse_yaml", "validate_schema", "monte_carlo", "cvx",
        "ledger_append", "ledger_verify", "sensitivity", "falsify",
    ],
    "axioms": [
        "no_claim_without_falsification",
        "no_external_side_effect_without_human_owner",
        "no_truth_assertion_without_receipt",
    ],
    "phi_constant": 0.6180339887,
}


def fingerprint(seed: Dict[str, Any]) -> str:
    """Stable SHA-256 of the seed, used as the MMNB identity anchor."""
    return hashlib.sha256(
        json.dumps(seed, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
