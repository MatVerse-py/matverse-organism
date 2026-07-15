# Architecture: 12 organs + 3 constitutional physics (v3.8.0)

The MatVerse Organism v3.8.0 is decomposed into **12 constitutional
organs** in a single cycle, plus **3 constitutional-physics objects**
that govern the laws under which the cycle operates.

This document supersedes the v3.0.0 "8+1 organs" framing, which
remains valid as a simplified view of the cognitive layer.

## The 12 constitutional organs

| # | Organ                      | Module                              | Role |
|---|----------------------------|-------------------------------------|------|
| 1 | MMNB                       | `matverse.mmnb`                     | Causal memory; seed of the next cycle |
| 2 | Cassandra / MetaCortex     | `matverse.cassandra`, `metacortex`  | Cognitive interpretation + level-3 learning |
| 3 | COG (Campo de Hipóteses)   | `matverse.organism`                 | Hypothesis field |
| 4 | Invariants                 | `matverse.invariants`               | Fail-closed constitutional gate (I1..I8) |
| 5 | Laws                       | `matverse.laws`                     | Versioned operational policies (LW1..LW8) |
| 6 | UMJAM                      | `matverse.umjam`                    | Admissible mutation (spec → transmutation) |
| 7 | SVCA                       | `matverse.svca`                     | Application video-capsule (proof bundle) |
| 8 | Closure                    | `matverse.closure`, `closure_macro` | Closure compiler (4-projections + 2 macro) |
| 9 | Atlas                      | `matverse.atlas`                    | Live cartographic projection |
| 10 | Thermodynamic Cortex      | `matverse.thermo`                   | Energy, PBR, regenerative accounting |
| 11 | Captals                    | `matverse.captals`                  | Continuity allocator + M-bit + proof chain |
| 12 | Existential Processes      | `matverse.existential`              | Metabolism, autopoiesis, apoptosis, antifragility, homeostasis |

## The 3 constitutional physics (NEW in v3.8.0)

| Object                       | Module                              | Definition |
|------------------------------|-------------------------------------|------------|
| GTHDL Hamiltonian            | `matverse.hamiltonian`              | dρ/dt = -i [Ĥ_Σ, ρ] with Ĥ_Σ = λ_Ω·Ω̂ + λ_Ψ·Ψ̂ + λ_C·Ĉ + λ_T·T̂ |
| Riemannian Memory Manifold   | `matverse.riemannian`               | M = (O, R, g, Φ, ρ) — metric, curvature, flow, density |
| Epistemic State Machine      | `matverse.epistemic`                | 8 states (NULL/OBS/INF/HYP/EVD/ADM/CON/ESCALATE) + Dempster-Shafer + Dung |

## The constitutional object (NEW in v3.8.0)

- **Formal MNB (5-tuple)**: `matverse.mnb_formal` —
  `m = (e, Ψ, C, τ, h)`, value density `ρ = Ψ·τ/C`,
  with the **ThermodynamicGate** that selects the unit minimizing
  the Hamiltonian of the system.

## The summary scalar (NEW in v3.8.0)

- **Omega Score Ω**: `matverse.omega` —
  `Ω = (C_inv · PBR_n · R_rec_n · A_aut · F_ant)^(1/5)`, all dims
  normalized to [0, 1]. The single number that summarizes the
  viability of the whole organism.

## The cycle

```
MMNB (1)   ──► Cassandra / MetaCortex (2)  ──► COG (3)
                ──► Invariants (4) + Laws (5)  [gate]
                ──► UMJAM (6)  ──► SVCA (7)  ──► Closure (8)
                ──► Atlas (9)   [update]
                ──► Thermo (10) [receipt]
                ──► Captals (11) [M-bit]
                ──► Existential (12) [metabolism + apoptosis checks]
                ──► next MMNB (1)
```

The constitutional physics (GTHDL, Riemannian, Epistemic) are not
cycle steps — they are the *laws* under which every step operates.
The Riemann manifold governs how memory is shaped; the GTHDL
Hamiltonian governs how the organism evolves; the Epistemic state
machine governs how hypotheses are believed.

## v3.0 → v3.8 evolution

| Version | Organs            | Physics | Object                | Score |
|---------|-------------------|---------|-----------------------|-------|
| v3.0.0  | 8+1               | —       | —                     | —     |
| v3.1.0  | + Invariants      | —       | —                     | —     |
| v3.2.0  | + SVCA + Atlas    | —       | —                     | —     |
| v3.3.0  | + Existential     | —       | —                     | —     |
| v3.4.0  | + Thermo          | —       | —                     | —     |
| v3.5.0  | + Captals         | —       | —                     | —     |
| v3.6.0  | + Closure Macro   | —       | —                     | —     |
| v3.7.0  | + MMNB + Capability + Probes + Adaptation | — | — | — |
| **v3.8.0** | (12 organs)   | **+3 constitutional physics** | **+ Formal MNB (5-tuple)** | **+ Ω** |

## Out of scope (by design)

- Public CAPT token issuance (HOLD on legal review)
- Blockchain anchor (PREPARED_NOT_BROADCAST, requires human)
- Zenodo DOI / GitHub Release tag / Hugging Face upload (PREPARED, requires human)
- Independent machine replay (requires second operator)
