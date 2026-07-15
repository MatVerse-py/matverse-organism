# Claims Policy — MatVerse OSX v0.1

## What this release **IS**

- A **constitutional surface**. Every organ, physics, and invariant
  defined in `matverse-organism` v3.8.0 is visible in this UI.
- A **Figure Lab** with deterministic SVG renderers for 7 of the 14
  canonical categories, plus a Visual Ω-Gate.
- A **Cognitive Canvas** with the 7 node shapes mapped to the 8
  epistemic states from the v0.2 kernel.
- An **in-browser demo** of the FullOrganismRunner for the v3.8.0
  cycle (genesis MMNB → Cassandra → COG → invariants → UMJAM → SVCA
  → closure → thermo → Ω → new MMNB).
- A **self-contained** package: no CDN, no remote APIs, no analytics,
  no cookies, no fonts loaded from the network.

## What this release **IS NOT**

- **NOT a production runtime.** The actual organism runs in the
  Python package `matverse-organism` v3.8.0 with 253/253 tests.
- **NOT an LLM.** The "Cassandra" command bar is a local rule router.
- **NOT a wallet.** No blockchain, no tokens, no payments.
- **NOT multi-user.** Single tab, single operator, in-memory state.
- **NOT authenticated.** The Human Node avatar is a visual
  representation only; it is not a session, not a signature, not a
  key.
- **NOT persistent.** Refresh resets everything (except the
  Cognitive Canvas, which can be exported/imported as JSON).

## Specific claims the v0.1 UI makes

| Claim                                                           | Verifiable? | Source                                |
|-----------------------------------------------------------------|-------------|----------------------------------------|
| "12 constitutional organs"                                      | YES         | matverse.canonical.CONSTITUTIONAL_ORGANS_V3_8 |
| "3 constitutional physics (GTHDL / Riemannian / Epistemic)"    | YES         | matverse.canonical.CONSTITUTIONAL_PHYSICS_V3_8 |
| "8 invariants I1..I8 (fail-closed)"                            | YES         | matverse.invariants                    |
| "5-tuple MNB m = (e, Ψ, C, τ, h)"                              | YES         | matverse.mnb_formal.FormalMNB          |
| "Ω = (C_inv · PBR/30 · R_rec/5 · A_aut · F_ant)^(1/5)"        | YES         | matverse.omega.omega_score             |
| "ρ = Ψ·τ/C"                                                     | YES         | matverse.mnb_formal.FormalMNB.value_density |
| "GTHDL: dρ/dt = -i[Ĥ_Σ, ρ]"                                    | YES         | matverse.hamiltonian                   |
| "M = (O, R, g, Φ, ρ)"                                            | YES         | matverse.riemannian                    |
| "8 EpistemicStates: NULL/OBS/INF/HYP/EVD/ADM/CON/ESCALATE"     | YES         | matverse.epistemic                     |
| "M-bit uses (Q·R·T·V·E·H)^(1/6)·(1-risk)"                     | YES         | matverse.captals.MBit                  |
| "FullOrganismRunner wires the 12 organs in one cycle"           | YES         | matverse.runner                        |
| "253/253 unit tests pass in v3.8.0"                            | YES         | `python -m unittest discover -s tests` |
| "All 4 publications remain PREPARED_NOT_PUBLISHED"              | YES         | matverse.publishers                    |

## Specific claims the v0.1 UI does **NOT** make

- Does NOT claim the organism is "deployed to production" (HOLD)
- Does NOT claim a public blockchain anchor (HOLD)
- Does NOT claim an independent machine replay (HOLD)
- Does NOT claim a public CAPT token (HOLD)
- Does NOT claim a live Zenodo / GitHub Release / HF publication (HOLD)
- Does NOT claim "Cassandra" is an LLM (it is a local rule router)
- Does NOT claim Cassandra is autonomous (it routes to local handlers)
- Does NOT claim the figure lab is "AI-generated" (it is deterministic SVG)

## Update discipline

If any of the verifiable claims above changes in the Python package
(`matverse-organism`), the v0.1 OSX must be updated to reflect the
new state. The version of OSX is coupled to the version of the
Python package it mirrors.
