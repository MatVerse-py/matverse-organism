# Limits

The MatVerse Organism v3.0.0 is honest about what it cannot do. The
following limits are part of the contract, not work-in-progress.

## It does NOT solve "any problem"

Problems that are:

- **Prohibited** (e.g. requests to produce malware, weapons, or
  exploitative material) are hard-gated at the classifier and never
  produce a `next_test`.
- **Physically infeasible** (e.g. "faster than light", "perpetual
  motion") are hard-gated.
- **Out of scope** (the problem explicitly says "out of scope") are
  hard-gated.
- **Undecidable** (e.g. the Halting problem, the Entscheidungsproblem)
  are hard-gated.
- **Intractable** (e.g. brute-force search spaces > 10⁹) are surfaced
  for human review.

## It does NOT handle non-quantitative claims

A hypothesis must have a `falsification_criteria` string that the
Organism can evaluate. Statements like "the design is elegant" do not
become tests. The user is expected to translate them into a
quantitative form (e.g. "Cyclomatic complexity < 10").

## It does NOT execute external side-effects

URANO defaults to `network="denied"` and `executor_mode="local_sandbox"`.
There is no built-in executor that can push to a remote service,
modify a database, or call a third-party API. If you need an effect
in the world, the Organism returns `HUMAN_REVIEW_CANDIDATE`.

## It does NOT prove factual truth

The ledger proves **local integrity** of the chain of decisions.
It does NOT prove:

- that the inputs were true;
- that the chosen strategy was correct in retrospect;
- that the Monte Carlo distributions match reality;
- that the Metacortex's recommendation is optimal.

The Organism is a method for structuring a decision under uncertainty,
not a method for replacing the decision.

## It does NOT replace domain experimentation

Monte Carlo propagates the **declared** uncertainty of the inputs.
It does not generate evidence from the world. For that, you need
real measurements, real users, and real time.

## It does NOT replace MLflow / DVC / LangGraph

These tools excel at:

- MLflow: tracking executions after they happen.
- DVC: versioning data and pipelines.
- LangGraph: orchestrating long-running agents.

The Organism composes with them. It does not subsume them. See the
`product_strategy.md` document for the integration story.

## What it DOES promise

- The Organism never invents a false PASS — a hypothesis either has
  a recorded `PASS` or a `REFUTED_PRESERVED`. There is no
  "definitely maybe".
- The Ledger never silently rewrites — `verify()` is a deterministic
  walk of the chain.
- The Metacortex never overrides a human gate — its output is a
  recommendation, not an instruction.
- Every run is reproducible given the same seed.
