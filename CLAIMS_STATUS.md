# Claims Status — MatVerse v3.8.0

This document records, **per claim**, the verification status in
v3.8.0. It exists to honor the constitutional principle
**"coerência crescente não é evidência crescente"** (growing
coherence is not growing evidence).

Each claim has one of four states:

- **STABLE** — code-backed, test-backed, reproducible
- **NEW** — new in v3.8.0, test-backed, scope-limited (stdlib only)
- **PROTOTYPE** — code exists, basic tests pass, but explicit
  limitations are documented
- **HOLD** — claimed by the corpus, not implemented in v3.8.0

## I. Constitutional surface

| Claim | State | Evidence |
|-------|-------|----------|
| 8 constitutional laws LW1..LW8 | STABLE | `tests/test_laws.py` |
| 8 fail-closed invariants I1..I8 | STABLE | `tests/test_invariants.py` |
| 8 thermodynamic laws L1..L8 | STABLE | `tests/test_thermo_captals.py` |
| 12 constitutional organs | STABLE | `tests/test_canonical.py` |
| 3 constitutional physics | STABLE | `tests/test_canonical.py` |
| 5 Captals layers (MNB, Mem-bit, M-Bit, CAPT, LCU) | STABLE | `matverse/captals.py` + docs |

## II. Objects (v3.8.0)

| Claim | State | Evidence |
|-------|-------|----------|
| 5-tuple MNB m = (e, Ψ, C, τ, h) | NEW | `tests/test_mnb_formal.py` (16 tests) |
| Value density ρ = Ψ·τ/C | NEW | unit-tested |
| MNB tamper detection (h recomputed) | NEW | unit-tested |
| GTHDL Hamiltonian Ĥ_Σ = λ_Ω·Ω̂ + λ_Ψ·Ψ̂ + λ_C·Ĉ + λ_T·T̂ | NEW | `tests/test_hamiltonian.py` (14 tests) |
| Master equation dρ/dt = -i[Ĥ_Σ, ρ] | NEW | Taylor expansion only; closed-form for diagonal H |
| Riemannian manifold M = (O, R, g, Φ, ρ) | NEW | sparse 4-tensor; `tests/test_riemannian.py` (12 tests) |
| Geodesic distance via metric tensor | NEW | unit-tested |
| 8 EpistemicState values | NEW | `tests/test_epistemic.py` (12 tests) |
| Dempster-Shafer with conflict preservation | NEW | unit-tested |
| Dung preferred extensions (conflict-free + self-defending) | NEW | unit-tested (v3.8.0 adds conflict-free check) |
| IRC = 1 - H/log(2) | NEW | unit-tested |
| Normalized Ω score (5-dim, all in [0,1]) | NEW | `tests/test_omega.py` (10 tests) |
| Ω validation against canonical closure v3.6 (0.78 < Ω < 0.85) | NEW | `tests/test_omega.py::test_canonical_closure_v36` |
| M-Bit 6-dim geometric score (Q·R·T·V·E·H)^(1/6)·(1-risk) | STABLE | `tests/test_thermo_captals.py` (uses 6 dims) |

## III. Organs (already present in v3.7.0)

| Claim | State | Evidence |
|-------|-------|----------|
| Hypothesis field (Campo de Hipóteses) | STABLE | `tests/test_organism.py` |
| UMJAM transmutation (spec → result) | STABLE | `tests/test_organism.py` |
| URANO (legacy) | STABLE | `tests/test_organism.py` |
| SVCA proof capsule | STABLE | `tests/test_organism.py` |
| Closure compiler (v3.0) | STABLE | `tests/test_organism.py` |
| Closure macro compiler (v3.6) | STABLE | `tests/test_closure_macro.py` |
| Atlas (cartographic projection) | STABLE | `tests/test_organism.py` |
| Metacortex (L3 learning) | STABLE | `tests/test_organism.py` |
| Existential processes (5) | STABLE | `tests/test_organism.py` |
| Captals engine (M-Bit + ProofChain + LCU) | PROTOTYPE | `tests/test_thermo_captals.py` |
| Capability registry (15 ACTIVE builtins) | STABLE | `tests/test_capability.py` |
| MMNB first-class persistent memory | STABLE | `tests/test_mmnb_adaptation.py` |
| Probes (RAPL, NVML, Declared) | PROTOTYPE | Linux-only; fallback to Declared everywhere else |
| Adaptation loops (Metacortex, Apoptosis, Autopoiesis) | PROTOTYPE | new in v3.7.0; integration-tested |
| CrossRunOrganism | PROTOTYPE | new in v3.7.0 |

## IV. Operational claims (HOLD — out of v3.8.0 scope)

| Claim | State | Why HOLD |
|-------|-------|----------|
| Real RAPL sensor data (not declared) | HOLD | requires Linux + Intel hardware in CI |
| Real NVML GPU sensor data | HOLD | requires NVIDIA + pynvml in CI |
| TACE scoring (support/conflict/uncertainty) | HOLD | requires `cassandra-tace-skill` increment |
| H-Axis mutation library | HOLD | requires perturbation corpus |
| Shadow Evaluator with real tests | HOLD | requires P2 → P3 step in P0-P4 path |
| Independent machine replay (second operator) | HOLD | constitutional position: human-authorized |
| Blockchain anchor (Sepolia) | HOLD | constitutional position: human-authorized |
| Zenodo DOI publication | HOLD | constitutional position: human-authorized |
| GitHub Release tag | HOLD | constitutional position: human-authorized |
| Hugging Face dataset upload | HOLD | constitutional position: human-authorized |
| Public CAPT token issuance | HOLD | requires legal review per jurisdiction |
| Captals × Gate genesis layer (full) | HOLD | lives in historical Captals / SuperKernel / CaptalsPrimeChain repos |
| Full Riemann 4-tensor (not sparse) | HOLD | requires numpy/scipy numeric backend |
| GTHDL closed-form for off-diagonal H | HOLD | requires numeric eigenvalue solver |

## V. What changed in v3.8.0 vs the previous audit

The previous audit (`matverse-audit-2026-07`, audit topic) flagged
that the corpus demands things v3.7.0 lacked. v3.8.0 addresses
**9 of 14** of those demands as **NEW** (test-backed, stdlib-limited):

- 5-tuple MNB ✓
- GTHDL Hamiltonian ✓
- Riemannian manifold (sparse) ✓
- 8 EpistemicStates ✓
- Dempster-Shafer ✓
- Dung extensions ✓
- IRC metric ✓
- Normalized Ω score ✓
- 12-organism constitutional taxonomy ✓

The remaining **5 demands** remain HOLD:

- Full Riemann 4-tensor (numeric)
- TACE scoring
- H-Axis mutation library
- Shadow Evaluator
- Captals × Gate genesis layer (in the historical repos)

## VI. The P0-P4 path forward

The corpus audit recommends the following P0-P4 path:

- **P0** — stabilize (achieved)
- **P1** — spec the Adaptation Loop (in progress: v3.7.0 +
  v3.8.0's `AdaptationMetacortex` + `ApoptosisScheduler` +
  `AutopoiesisGenerator`)
- **P2** — Capability Registry minimal (achieved in v3.7.0)
- **P3** — Shadow Evaluator with real tests (HOLD)
- **P4** — calculate new metrics only after P3 is real (HOLD)

**The v3.8.0 PR is open. P3 and P4 are NOT in v3.8.0. They are
the natural next increments.** The operator should not merge v3.8.0
as if it ships P3 or P4.
