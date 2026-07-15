# MatVerse architectural lineage

**Canonical claim** (from `matverse_repo_lineage_audit_2026-06-21.md`):

> The MatVerse did not evolve by replacing ideas. It evolved by
> deepening the resolution.

This document records the seven layers in the order they were
introduced and the responsibility each one holds. It exists because
v3.8.0 was published as a single release, but the layers it bundles
were not built on the same day. **Reading them as if they had the
same maturity is the most common source of over-claiming.**

## The seven layers (in order of introduction)

| # | Layer | Introduced | Responsibility |
|---|-------|------------|----------------|
| 1 | **Captals × Gate** (Genesis) | early 2025 | Economy of value, decision, and continuity under admissibility rules |
| 2 | **PoSE + anchors + ledger** | early 2025 | Memory and proof (append-only, hash-chained) |
| 3 | **Cassandra + M-CSQI + coherence** | mid 2025 | Qualification (claim extraction, grounding, TACE scoring, gating) |
| 4 | **MNB + Mem-bit** | late 2025 | Causal granularity (the unit became decomposable) |
| 5 | **M-Bit** | 2026 Q1 | Advance guarantee (the unit of progress, not just receipt) |
| 6 | **Paper-Contract** | 2026 Q1 | The root formal artifact of a trail |
| 7 | **Captals DeSci (current Captals)** | 2026 Q2 | Allocation to research and technology trails |

## Reading the v3.8.0 release through this lineage

The v3.8.0 release (`matverse-organism`) bundles 12 organs, 3
constitutional physics, and the canonical Ω score. **The release
must not claim equal maturity for all of these layers.** Here is
the honest map:

| v3.8.0 organ / physics                  | Layer | Maturity in v3.8.0                |
|------------------------------------------|-------|------------------------------------|
| `matverse.laws` (LW1..LW8)              | 1     | **stable** — versioned, tested     |
| `matverse.ledger`                        | 2     | **stable** — hash-chained, tested  |
| `matverse.invariants` (I1..I8)           | 3     | **stable** — fail-closed, tested   |
| `matverse.cassandra` + `axis8`          | 3     | **prototype** — basic operations  |
| `matverse.mmnb` (causal memory)          | 4     | **stable** — file-backed, verified |
| `matverse.mnb_formal` (5-tuple)          | 4     | **new in v3.8.0** — clean spec     |
| `matverse.captals` (M-Bit, ProofChain)   | 5     | **prototype** — see HOLD notes     |
| `matverse.closure_macro`                 | 6     | **stable** — tested                |
| `matverse.hamiltonian` (GTHDL)           | 7     | **new in v3.8.0** — clean spec, stdlib-limited |
| `matverse.riemannian` (manifold)         | 7     | **new in v3.8.0** — sparse approx. |
| `matverse.epistemic` (Dempster-Shafer)   | 3     | **new in v3.8.0** — clean spec     |
| `matverse.omega` (Ω score)               | 5+7   | **stable formula** — HOLD on real probes |

**Anything listed as "stable" is test-backed (253/253 in v3.8.0).
Anything listed as "new in v3.8.0" is test-backed but limited to
the stdlib scope (no numpy/scipy). Anything listed as "prototype"
is acknowledged as such in the code.**

## What v3.8.0 does **NOT** claim

- That the GTHDL Hamiltonian is a production numerical solver (it
  is a Taylor-expansion approximation, valid for short `dt`).
- That the Riemannian 4-tensor is a full Riemann manifold (it is a
  sparse approximation, valid for stdlib memory bounds).
- That the Ω score is sensor-backed (it is `PBR_n × A_aut × F_ant ×
  ...` where each is a declared value, not a measurement).
- That the Captals × Gate genesis layer is fully implemented in
  this Python package (the genesis lives in the historical
  Captals / SuperKernel / CaptalsPrimeChain repos; this package
  only carries the M-Bit + ProofChain + LCU sublayer that emerged
  from it).
- That the organism is on-chain (all publications remain
  `PREPARED_NOT_PUBLISHED`).

## The P0-P4 path (per the corpus)

The corpus audit recommends that future increments follow:

- **P0** — stabilize the Go simulator and the Python package
  (achieved in v3.7.0, held in v3.8.0)
- **P1** — specify the Adaptation Loop as a future architecture
  (in progress in v3.8.0's `AdaptationMetacortex` + `ApoptosisScheduler` + `AutopoiesisGenerator`)
- **P2** — implement the Capability Registry minimal (achieved in v3.7.0)
- **P3** — Shadow Evaluator with real tests (NOT IMPLEMENTED — HOLD)
- **P4** — calculate new metrics only after P3 is real (NOT IMPLEMENTED — HOLD)

**P3 and P4 are documented as HOLD in v3.8.1.** They are the natural
next increments.

## Read this before citing v3.8.0

If you cite v3.8.0 in a paper, release note, or public statement,
read the table above first. The constitutional position is: **the
organism prepares, the operator signs, the world witnesses**. A
release that overstates its maturity fails the constitutional
position before it fails the technical review.
