# The Closure Macro Compiler

A closure is the canonical object that ties together a complete organism-level cycle. It is the four projections of a single evolutionary event, plus (in v3.6+) the thermodynamic and regenerative projections.

## Six projections

| Projection      | What it contains                                          | Audience       |
|-----------------|-----------------------------------------------------------|----------------|
| Paper           | Problem, claim, falsification, evidence, limitations     | Zenodo         |
| Code            | Repository, commit, release tag, build receipt             | GitHub Release |
| Execution       | Run id, environment, receipt, replay status, metrics      | Hugging Face   |
| Canonization    | Manifest hash, Merkle root, gate state, lineage           | Blockchain      |
| Thermodynamic   | PBR, regenerative ratio, energy, carbon                    | ThermoCortex   |
| Regenerative    | Avoided/recovered/renewable/ecological, PBR                | Captals        |

## Three scales (fractal)

| Scale | Use case                                            | Example                          |
|-------|------------------------------------------------------|----------------------------------|
| MICRO | A single mutation                                    | A new rule in `organism.py`      |
| MESO  | A capability or release                              | v3.7.0 release of URANO Metabolic Runtime |
| MACRO | An organism generation                               | MatVerse Organism v1             |

All three scales emit the same projections. The signature is the only thing that changes.

## Gate states (canonization)

| State                          | Meaning                                           |
|--------------------------------|---------------------------------------------------|
| `CLOSURE_CANDIDATE`            | Bundle built but not yet admissible               |
| `CLOSED`                       | All four contracts satisfied                      |
| `REPLAYED_INDEPENDENT`         | A second operator has run the same SVCA          |
| `WITNESSED_EXTERNAL`           | A blockchain anchor exists for this closure      |

The constitutional state of v3.7.0 is `REPLAYED_INDEPENDENT` for deterministic capabilities. `WITNESSED_EXTERNAL` requires a human-authorized blockchain broadcast.

## Parent closure lineage

Every closure has an optional `parent_closure_id`. The lineage forms a tree:

```
MV-CLOSURE-0001 (genesis)
  ├─ MV-CLOSURE-0002 (capability release)
  │    └─ MV-CLOSURE-0003 (micro: bugfix)
  └─ MV-CLOSURE-0004 (capability release)
```

Supersession is recorded via the `supersedes` field. The Atlas reflects this lineage.

## The four contracts (from the canon)

### Scientific contract

Paper declares: problem, hypothesis, context, contribution, evidence, contradictions, falsification, limitations, relation to previous, next hypotheses.

### Technical contract

Code contains: version, license, pinned dependencies, build, tests, configuration, schema, verifier, run instructions, rollback.

### Execution contract

Execution preserves: inputs, environment, seed, commands, duration, results, metrics, errors, logs, receipts, replay conditions.

### Canonization contract

Canonization contains: deterministic manifest, hashes, Merkle root, links between artifacts, authors and contributions, external identifiers, epistemic status, operational status, supersession policy, relation to previous closure.

A closure is `CLOSED` only when all four contracts are satisfied.
