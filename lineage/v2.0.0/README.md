# MatVerse Organism v2.0.0 — preserved lineage

This directory preserves the source of the v2.0.0 release
(2026-07-07) for historical reference. **It is not used by v3.0.0.**
It is here because the MatVerse governance rule is:

> A version is never deleted. It remains a part of the lineage so
> that the organism can learn from its own history.

The v2.0.0 SHA-256 (of the skill bundle) is:
`e70524eef98b2f7712023ed47320ed612668d830b85855e9f4eddaf212e2fdad`

## What v2.0.0 was

- A single-organ skill (`matverse-organism`).
- Campo de Hipóteses with 8 Leis, 8 AXIS-8 lenses, Monte Carlo + CVaR.
- Hash-chained ledger.
- 11/11 unit tests passing.
- `report.json`, `MANIFEST.json`, and `SKILL.md` produced.
- `PASS_LOCAL_EXECUTABLE / HOLD_EXTERNAL_VALIDATION`.

## What v3.0.0 added on top

- **URANO Metabolic Runtime** — compiles hypotheses into executable
  ExperimentContracts.
- **Closure Compiler** — verifies a complete cycle.
- **Metacortex** — level-3 learning: method recommendation by class.
- **`hypo` CLI** — three commands, integration-tested end-to-end.
- **46/46 unit tests** (vs. 11/11 in v2.0.0).
- **Apache 2.0 license** (the v2.0.0 distribution did not include an
  explicit license file).
- **CITATION.cff** for Zenodo.
- **`mmnb_seed.json`** declaring the v3 starting state.

## Why preserve

- To make the v2 → v3 evolution auditable, like any other hypothesis
  transition in the Organism.
- To let future maintainers answer: "why did we add URANO before
  Metacortex? why was the licensing changed? why was the test count
  quadrupled?" without external guesswork.
- To keep the option of `pip install matverse-organism==2.0.0` open
  via this repository's `tags`.

The v2.0.0 source here is the **published** structure of the v2.0.0
skill. The actual bytes of the original bundle are not redistributed
verbatim; the canonical structure is reconstructed from the public
descriptions of v2.0.0 in the conversation and audit logs of
2026-07-07.
