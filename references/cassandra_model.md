# Cassandra — informational model, not persona

**Canonical claim** (from `Texto colado(926).txt`):

> Cassandra is defined as an **informational model** of the MatVerse
> (not a single persona or decision-maker). Its facets are
> implemented as **separated skills** that form a team of responsible
> operators, each with strict scope.

This document clarifies what `matverse.cassandra.Cassandra` is and
is not, and how it fits with the rest of the organism.

## The model: a team of skills, not a single LLM

In the corpus, the "Cassandra" surface is decomposed into:

| Skill | Responsibility | v3.8.0 module |
|-------|----------------|----------------|
| `cassandra-interpreter` | Extract claims from text | partial in `matverse.cassandra` |
| `atlas-grounding` | Validate claims against the constitutional atlas | partial in `matverse.atlas` + `matverse.invariants` |
| `tace-evaluator` | TACE scoring (support, conflict, uncertainty) | NOT IMPLEMENTED — HOLD |
| `h-axis-adversarial-evaluator` | H-Axis stability under mutation | partial in `matverse.axis8` (REDTEAM lens) |
| `omega-gate-epistemico` | Epistemic Ω-Gate (deterministic) | partial in `matverse.invariants` + `matverse.omega` |
| `ledger-replay` | Append-only replay verification | `matverse.ledger` + `matverse.replay` |
| `impact-briefing` | Per-problem briefing | NOT IMPLEMENTED — HOLD |

**v3.8.0 implements about 4 of 7 skills. The remaining 3 are
documented HOLD.** This is honest: the v3.8.0 release does not
contain a "Cassandra" — it contains the foundation for one.

## TACE (claim classification)

The corpus defines TACE as:

- **support_score** = ∑ log-likelihood(ev_i)  over evidence
- **conflict_score** = max(0, -log BF)  where BF is the Bayes factor
- **uncertainty_score** = posterior entropy

v3.8.0 does **not** compute TACE explicitly. The closest equivalent
is `dempster_combine` in `matverse.epistemic`, which combines
belief, uncertainty, and conflict in a Dempster-Shafer frame. TACE
is the next increment.

## H-Axis adversarial stability

The corpus defines H-Axis as:

> H = support - conflict - mutation_penalty + bonus

with a mutation test that perturbs the input and re-evaluates. The
v3.8.0 `axis8` module has a REDTEAM lens that is the closest
analogue, but the mutation perturbation library is not bundled.

## Ω-Gate determinism

The corpus requires that the gate produce a **deterministic**
verdict: `hash(payload + version_notes)` must reproduce. v3.8.0's
`matverse.invariants.evaluate()` is pure-functional and
deterministic for a given `Problem` and `Policy`. This is the
canonical gate.

## What the OSX v0.1 "Cassandra command bar" is

The bottom-bar input in the OSX UI is a **local rule router**, not
an LLM. It pattern-matches against:

- `^(crie|criar|nova?)\s+hip[oó]tese`  → create a hypothesis cell
- `^(rode|rodar|run)`                   → would invoke URANO (HOLD)
- `^(explique|explain)`                → explain a selected cell (HOLD)
- `omega`                              → recompute the Ω score
- anything else                        → log the command, no action

This is **not** a "Cassandra". It is a demo of the routing surface
that a future local-LLM or remote LLM would populate.

## What v3.8.0 does NOT claim about Cassandra

- That it is a single persona with a single model behind it
- That it is autonomous
- That it has access to a frontier LLM
- That it can generate images, audio, or other modalities
- That it has long-term memory beyond the MMNB lineage

## What v3.8.0 DOES claim

- That the `matverse.cassandra.Cassandra` class provides a clean
  hook for the team-of-skills pattern
- That the `matverse.axis8.AXIS8` lenses can be used as the
  H-Axis perturbation backbone
- That the `matverse.ledger` + `matverse.replay` chain satisfies
  the deterministic-replay requirement of the Ω-Gate
- That the remaining skills (TACE, Impact Briefing) are
  **HOLD** and require the next release cycle
