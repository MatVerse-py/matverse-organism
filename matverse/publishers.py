"""
matverse.publishers
===================

The publication layer. Prepares canonical metadata for the four
external surfaces of a closure:

  - Zenodo         (scientific memory)
  - GitHub Release (technical genotype)
  - Hugging Face   (empirical expression)
  - Blockchain     (external witness)

This module ONLY prepares the metadata. It does NOT publish. The
organism's constitutional position is:

  "PREPARED_NOT_PUBLISHED" / "PREPARED_NOT_BROADCAST"

until an explicit external operation is performed by a human operator
or by a contract the operator has authorized.

Each publisher returns a serializable dict that the operator can
review, sign, and submit.
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .closure_macro import ClosureBundle


# ---------------------------------------------------------------------------
# Zenodo metadata (subset of the official schema)
# ---------------------------------------------------------------------------

def zenodo_metadata(bundle: ClosureBundle,
                    creators: List[Dict[str, str]],
                    access_right: str = "open") -> Dict[str, Any]:
    return {
        "title": bundle.paper.title,
        "upload_type": "publication",
        "publication_type": "report",
        "description": bundle.paper.abstract,
        "creators": creators,
        "access_right": access_right,
        "version": bundle.version,
        "communities": [{"identifier": "matverse"}],
        "keywords": [
            "matverse", "organism", "hypothesisops",
            "falsification", "regenerative",
        ],
        "custom": {
            "matverse": {
                "closure_id": bundle.closure_id,
                "parent_closure_id": bundle.parent_closure_id,
                "scale": bundle.scale,
                "manifest_hash": bundle.canonization.manifest_hash,
                "merkle_root": bundle.canonization.merkle_root,
                "state_epistemic": bundle.state_epistemic,
                "state_closure": bundle.state_closure,
            }
        },
        "status": "PREPARED_NOT_PUBLISHED",
    }


# ---------------------------------------------------------------------------
# GitHub Release metadata
# ---------------------------------------------------------------------------

def github_release_metadata(bundle: ClosureBundle,
                            repo: str,
                            tag_name: str) -> Dict[str, Any]:
    return {
        "repo": repo,
        "tag_name": tag_name,
        "name": f"{bundle.closure_id} — {bundle.paper.title}",
        "body": _render_release_body(bundle),
        "target_commitish": bundle.code.commit,
        "draft": True,
        "prerelease": False,
        "custom": {
            "closure_id": bundle.closure_id,
            "parent_closure_id": bundle.parent_closure_id,
            "scale": bundle.scale,
            "manifest_hash": bundle.canonization.manifest_hash,
        },
        "status": "PREPARED_NOT_RELEASED",
    }


def _render_release_body(bundle: ClosureBundle) -> str:
    lines = [f"## {bundle.paper.title}", "",
             bundle.paper.abstract, "",
             f"- closure_id: `{bundle.closure_id}`",
             f"- parent_closure_id: `{bundle.parent_closure_id}`",
             f"- scale: `{bundle.scale}`",
             f"- organism: `{bundle.organism}` v`{bundle.version}`",
             f"- manifest_hash: `{bundle.canonization.manifest_hash}`",
             f"- merkle_root: `{bundle.canonization.merkle_root}`",
             f"- state_epistemic: `{bundle.state_epistemic}`",
             f"- state_closure: `{bundle.state_closure}`",
             "",
             "### Projections",
             "- Paper, Code, Execution, Canonization, Thermo, Regenerative",
             "",
             "### Notes",
             "Prepared locally. Replay independent, broadcast to external "
             "witness, and public publication are separate, human-authorized "
             "operations."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hugging Face metadata
# ---------------------------------------------------------------------------

def huggingface_metadata(bundle: ClosureBundle,
                         repo_id: str,
                         kind: str = "dataset") -> Dict[str, Any]:
    return {
        "repo_id": repo_id,
        "kind": kind,
        "card_content": _render_hf_card(bundle),
        "tags": ["matverse", "hypothesis", "evaluation", "regenerative"],
        "license": "apache-2.0",
        "private": False,
        "custom": {
            "closure_id": bundle.closure_id,
            "manifest_hash": bundle.canonization.manifest_hash,
            "replay_status": bundle.execution.replay_status,
        },
        "status": "PREPARED_NOT_PUBLISHED",
    }


def _render_hf_card(bundle: ClosureBundle) -> str:
    return f"""---
license: apache-2.0
tags:
  - matverse
  - hypothesis
  - regenerative
---

# {bundle.paper.title}

{bundle.paper.abstract}

- closure_id: `{bundle.closure_id}`
- manifest_hash: `{bundle.canonization.manifest_hash}`
- merkle_root: `{bundle.canonization.merkle_root}`
- replay_status: `{bundle.execution.replay_status}`

This dataset was produced by a MatVerse Organism closure. It is a
projection of the same canonical closure that produced the code
release and the paper. Please refer to the Zenodo deposition for
the canonical record.
"""


# ---------------------------------------------------------------------------
# Blockchain anchor (minimum object)
# ---------------------------------------------------------------------------

def blockchain_anchor(bundle: ClosureBundle,
                      network: str = "ethereum-mainnet") -> Dict[str, Any]:
    return {
        "network": network,
        "operation": "anchor",
        "payload": {
            "closure_id": bundle.closure_id,
            "manifest_hash": bundle.canonization.manifest_hash,
            "merkle_root": bundle.canonization.merkle_root,
            "scale": bundle.scale,
            "version": bundle.version,
            "ts": bundle.timestamp,
        },
        "tx_hash": None,                 # populated when broadcast
        "witness_proof": None,
        "constitutional_disclaimer": (
            "The blockchain witnesses that this anchor existed at this time "
            "in this network. It does NOT prove scientific truth, code "
            "quality, or exclusive human authorship."
        ),
        "status": "PREPARED_NOT_BROADCAST",
    }


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

@dataclass
class PublicationSet:
    closure_id: str
    zenodo: Dict[str, Any]
    github: Dict[str, Any]
    huggingface: Dict[str, Any]
    blockchain: Dict[str, Any]
    canonical_hash: str
    ts: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "closure_id": self.closure_id,
            "zenodo": self.zenodo,
            "github": self.github,
            "huggingface": self.huggingface,
            "blockchain": self.blockchain,
            "canonical_hash": self.canonical_hash,
            "ts": self.ts,
        }


def prepare_publication(bundle: ClosureBundle,
                        creators: List[Dict[str, str]],
                        github_repo: str,
                        github_tag: str,
                        hf_repo_id: str,
                        blockchain_network: str = "ethereum-mainnet") -> PublicationSet:
    z = zenodo_metadata(bundle, creators)
    g = github_release_metadata(bundle, github_repo, github_tag)
    h = huggingface_metadata(bundle, hf_repo_id)
    b = blockchain_anchor(bundle, blockchain_network)

    canonical = hashlib.sha256(
        json.dumps({"z": z, "g": g, "h": h, "b": b,
                    "cid": bundle.closure_id}, sort_keys=True, default=str).encode()
    ).hexdigest()

    return PublicationSet(
        closure_id=bundle.closure_id,
        zenodo=z, github=g, huggingface=h, blockchain=b,
        canonical_hash=canonical,
        ts=int(time.time()),
    )
