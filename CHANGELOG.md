
## [3.7.0] - 2026-07-14

### Added — Release v3.7.0 "Cross-run organism"

The organism now has real, persistent, cross-run capabilities. Where
v3.6.0 had the eight-plus-one organs but each run was independent,
v3.7.0 closes the cross-run feedback loops.

#### New modules
- `matverse.capability` — Contract-driven capability registry. 15
  built-in capabilities (echo, paired-metric, monte-carlo,
  sensitivity, ledger, axis8, json-validate, ast-diff, decompose,
  coverage, schema-infer, thermal-record, mbit-record,
  publish-metadata, plus paired-metric). Persistent to JSON. Supports
  supersession and revocation. Implements the v3.7.0 contract
  (inputs, outputs, cost, risk, permissions, tests, lineage).
- `matverse.mmnb` — MMNB causal memory as a first-class persistent
  object. Each MMNB has parent_id, lineage, generation, and
  fingerprint hash. Tampering with the JSON file fails `verify()`.
  The store is on disk, indexed by id and ordered by generation.
- `matverse.adaptation` — Three adaptation loops:
  - `AdaptationMetacortex` — the Metacortex now writes
    recommended_strategy + weights to the MMNB.
  - `ApoptosisScheduler` — retires capabilities whose failure rate
    exceeds a threshold over a grace window.
  - `AutopoiesisGenerator` — proposes a new capability from a gap,
    validates it, and registers it.
  - `CrossRunOrganism` — a new `Organism` subclass that consults
    the Metacortex before ranking.
- `matverse.probes` — Real hardware probes:
  - `DeclaredProbe` (default)
  - `RaplProbe` (Intel RAPL on Linux)
  - `NvmlProbe` (NVIDIA via pynvml)
  - `CompositeProbe`
  - `make_default_probe()` returns RAPL if available, else Declared.

#### Updated CLI
The `hypo` command now exposes every organ:
- `hypo organism run` — run the FullOrganismRunner
- `hypo invariants check` — evaluate the 8 invariants
- `hypo laws evaluate` — evaluate the 8 laws
- `hypo cassandra interpret` — produce a Cassandra reading
- `hypo svca replay` — re-run a SVCA's transmutation
- `hypo atlas show/health` — the live atlas
- `hypo thermo record/report` — thermodynamic accounting
- `hypo captals record/report` — Captals engine
- `hypo existential status` — existential processes
- `hypo mmnb show/lineage` — MMNB causal memory
- `hypo closure compile` — produce a closure bundle
- `hypo publish prepare` — prepare platform metadata

#### Infrastructure
- `.github/workflows/ci.yml` — CI across Python 3.8–3.12 with smoke tests
- `Dockerfile.v3` — multi-stage build (Go kernel + Python organ)
- `tools/release.sh` — reproducible release script
- `MANUAL.md` — operator manual
- `references/{invariants,thermo,captals,existential,closure_macro}.md`

#### Validation
- Compilação Python:          PASS
- Testes automatizados:       146/146 PASS (was 116 in v3.6.0)
- MMNB cross-run chain:      4 generations tested
- Capability registry:       15 ACTIVE builtins
- All 4 platform pubs:       PREPARED_NOT_PUBLISHED (by design)
- Pure stdlib:               yes (>= 3.8)

# Changelog

All notable changes to the MatVerse Organism are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).
The project adheres to [Semantic Versioning](https://semver.org/).

## [3.6.0] - 2026-07-14

### Added — Release v3.6.0 "Eight-plus-one organs"

The integrative cognitive layer now has all the organs required by
the canonical architecture, plus the existential processes that govern
the lifecycle of those organs.

#### New organs
- **`matverse.invariants`** — 8 fail-closed constitutional invariants
  (I1..I8). `InvariantViolation` halts the system.
- **`matverse.cassandra`** — cognitive interpretation layer.
  Produces a `CassandraReading` with competing claims, candidate
  falsifiers, metacognitive notes, and a self-assessed confidence.
- **`matverse.umjam`** — Universal MatVerse Joint of Admissible
  Mutation. Pure capability registry, NaN-rejecting, refuse on error.
- **`matverse.svca`** — S Vídeo-Cápsula de Aplicação. Proof capsule
  bundling input, config, environment, execution, result, metrics,
  hashes, receipt, and replay conditions.
- **`matverse.atlas`** — live cartographic projection of the
  organism: nodes, edges, kinds, states, lineage.
- **`matverse.thermo`** — ThermoCortex + 8 thermodynamic laws.
  Exergy, Carbon, PBR (Planetary Benefit Ratio), regenerative ratio.
  Pluggable Probe (Declared by default; SENSOR/ATTESTED/INDEPENDENT
  achievable by replacing the probe).
- **`matverse.captals`** — Captals engine + M-bit + Proof Chain
  (PoSE, PoCT, PoTM, PoLE) + Work Contract + LCU (LLM Compute Unit).
  M-bit geometric score prevents rewarding volume without utility.
- **`matverse.existential`** — Metabolism, Autopoiesis, Apoptosis,
  Antifragility, Homeostasis. Each is a first-class process, not a
  metaphor.
- **`matverse.closure_macro`** — fractal closure compiler. 4 + 2
  projections: Paper, Code, Execution, Canonization, Thermo,
  Regenerative. Micro / Meso / Macro scales.
- **`matverse.publishers`** — Zenodo, GitHub Release, Hugging Face,
  Blockchain anchor metadata. **PREPARED_NOT_PUBLISHED only**; the
  organism never publishes without an explicit human-authorized
  external operation.
- **`matverse.replay`** — independent replay verification. Advances
  `replay_status` from `LOCAL_REPLAYED` to `INDEPENDENT_REPLAYED`.
- **`matverse.runner`** — `FullOrganismRunner`, the canonical wiring
  of all organs. Returns a `FullOrganismResult` with closure, SVCA,
  Cassandra reading, organism report, publication set, replay report,
  thermodynamic receipt, M-bit, and Atlas snapshot.

#### Updated
- `__init__.py` exports all 68 public symbols.
- `urano.py` retained as a back-compat alias; the canonical organ is
  now `umjam.UMJAM`.
- 116 / 116 unit tests pass (was 46 / 46 in v3.0.0).
- README, CHANGELOG, CITATION, SKILL updated.

#### Validation
- `Compilação Python`:            PASS
- `Testes automatizados`:         116 / 116 PASS
- `End-to-end closure (echo)`:    closure=REPLAYED_INDEPENDENT
- `PBR demo (declared)`:          21.91
- `Pure stdlib`:                  yes (>= 3.8)
- `External publication`:         HOLD (PREPARED_NOT_PUBLISHED, by design)

## [3.0.0] - 2026-07-14

### Added — Release v3.0.0 "HypothesisOps wedge"

The integrative cognitive layer of the MatVerse ecosystem. This release
turns the v2.0.0 single-organ skill into a complete eight-plus-one organ
organism, with a CLI wedge that can land on a GitHub PR today.

#### Campo de Hipóteses (carried from v2.0.0, hardened)
- Deterministic Monte Carlo with explicit seed, P10/P50/P90, mean, std.
- CVaR(α=0.10) — expected value in the worst 10% of cases.
- Local one-at-a-time sensitivity, sorted by |Δ|.
- 8 Leis Constitucionais (phenomenon, experiment, science, contract,
  value, safety, heritage, ecosystem).
- 8 AXIS-8 lenses (TRUTHMODE, REDTEAM, UNLEARN, 80/20, HORMOZI,
  FUTUREYOU, /human, H-Axis).
- Fail-closed decision: `TEST_NEXT`, `HUMAN_REVIEW_CANDIDATE`,
  `HOLD_ACTION`, `REFUTED_PRESERVED`, `PROHIBITED_ACTION`, ...
- 46/46 unit tests pass (>= 22 required).

#### URANO Metabolic Runtime (new)
- `matverse.urano.URANO.compile(problem, hypothesis)` returns an
  `ExperimentContract` with executor mode, network policy, timeout,
  acceptance criteria, risk blast radius, reversibility, rollback.
- `matverse.urano.URANO.run(contract)` executes in a local sandbox,
  appends a Receipt, returns an `ExperimentResult`.
- No external side-effects: `network="denied"` is the default.

#### Closure Compiler (new)
- `matverse.closure.ClosureCompiler.run_full_cycle(problem)` verifies
  that a complete cognitive cycle (investigate → compile → run → receipt)
  has been executed. Returns `closed=True` only when all four steps
  recorded receipts in the same ledger.

#### Metacortex (new — level-3 learning)
- `matverse.metacortex.Metacortex.record(LearningRecord)` ingests a record.
- `Metacortex.profile_by_class()` aggregates per problem class.
- `Metacortex.recommend("CLI_adoption")` returns the
  `ClassProfile` with the strategy that has the best (pass_rate ×
  (1 − calibration_error)) score.
- Confidence grows with sample size and dominance.

#### Ledger (carried + extended)
- `kind`, `status`, and `timestamp` are now part of the chain hash.
- Tampering with any of those fields is detected by `Ledger.verify()`.

#### HypothesisOps CLI (new — the wedge)
- `hypo init --objective ... --n-hypotheses N` — bootstrap a problem file.
- `hypo resolve -i problem.json [--execute]` — run the organism
  (optionally the full cycle with URANO + Closure).
- `hypo promote --problem-class ... --strategy ...` — feed the
  Metacortex and read its recommendation.
- All three commands have integration tests (subprocess-based).

#### Schema (new, machine-readable)
- `schemas/problem.schema.json` — Problem contract.
- `schemas/hypothesis.schema.json` — Hypothesis contract.
- `schemas/experiment.schema.json` — ExperimentContract contract.
- `schemas/learning_record.schema.json` — LearningRecord contract.

#### MMNB seed (new)
- `mmnb_seed.json` declares the v3 starting state: 686 cells, 8
  capabilities, 3 axioms, phi constant 0.6180339887.
- `matverse.seeds.fingerprint(seed)` is its stable identity anchor.

#### Examples and validation
- `examples/cli_adoption.json` — three-hypothesis CLI adoption problem.
- `examples/h_offline.json` — single-hypothesis PRNG-determinism check.
- `validation/report.json` — output of the bundled example (full cycle).
- `validation/ledger.json` — hash-chained receipts.
- `validation/metacortex_recommendation.json` — Metacortex output.

#### Documentation
- `SKILL.md` — full contract (when to use, when not, API, examples).
- `README.md` — landing page.
- `LICENSE` — Apache 2.0.
- `pyproject.toml` — package metadata, `hypo` console script.
- `CITATION.cff` — Zenodo/GitHub-native citation.
- `references/architecture.md` — 8+1 organs model.
- `references/canonical_laws.md` — 8 Constitutional Laws explained.
- `references/limits.md` — what the organism cannot do.
- `references/product_strategy.md` — HypothesisOps positioning.
- `lineage/v2.0.0/` — preserved v2.0.0 source for the historical record.

### Changed (relative to v2.0.0)
- The skill is now installable as a Python package (`pip install -e .`)
  and exposes a `hypo` console script.
- The Organism's ranking function now normalises `information_gain`
  to [0, 1] so that a high-EV hypothesis cannot dominate safer ones.
- The 8 Constitutional Laws are evaluated deterministically against the
  Problem's `metadata` and Hypothesis list; no manual or external
  configuration is required.
- The Ledger's `verify()` returns `ok=True` only when the full chain
  (input + output + kind + status + timestamp) recomputes identically.

### Removed
- "Resolves any problem" framing. Replaced with a strict problem
  classifier that returns explicit `PROHIBITED_ACTION`,
  `PHYSICALLY_INFEASIBLE`, `OUT_OF_SCOPE`, `UNDECIDABLE_CANDIDATE`,
  `INTRACTABLE` states and refuses to proceed.
- Auto-execution of external side-effects. The system is `fail-closed`:
  effects are gated behind `HUMAN_REVIEW_CANDIDATE` and explicit
  ExperimentContract acceptance.

### Validation status
- `Compilação Python`:          PASS
- `Testes automatizados`:       46/46 PASS
- `Execução do exemplo`:        PASS (decision=HOLD, closure=closed)
- `Monte Carlo determinístico`: PASS (seed=42 reproduzível)
- `NaN / infinito`:             REJECTED
- `Ledger hash-encadeado`:      PASS
- `Detecção de adulteração`:    PASS
- `Validação externa`:          NOT_PERFORMED

## [2.0.0] - 2026-07-07

### Added
- Campo de Hipóteses (single-organ skill, Python stdlib only).
- 8 Constitutional Laws and 8 AXIS-8 lenses.
- Hash-chained Ledger.
- 11/11 unit tests, SHA-256 `e70524eef98b2f7712023ed47320ed612668d830b85855e9f4eddaf212e2fdad`.

### Preserved in `lineage/v2.0.0/`
The v2.0.0 source, schema, and tests remain in this repository under
`lineage/v2.0.0/`. They are not executed by v3.0.0 but remain a faithful
historical record of the previous organ's structure and tests.

[3.0.0]: #300---2026-07-14
[2.0.0]: #200---2026-07-07
