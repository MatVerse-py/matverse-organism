# Product strategy: HypothesisOps

The MatVerse Organism is not positioned as a chatbot, an LLM
framework, or an experiment tracker. It occupies a specific empty
niche we call **HypothesisOps**.

## The problem

Most product and engineering decisions are made on:

- intuition,
- LLM hallucinations,
- or over-engineered ADR documents that nobody reads.

There is no widely adopted tool that:

1. structures the decision as competing hypotheses;
2. records evidence for and against each;
3. requires a falsification condition;
4. runs the cheapest test that reduces the most uncertainty;
5. preserves failed hypotheses for institutional memory;
6. gives the next team a recommendation based on the history of
   similar problems.

The Organism does exactly those six things, locally, with the
Python standard library.

## Adjacent markets

| Adjacent               | Adjacent strength                          | What the Organism adds                                     |
|------------------------|--------------------------------------------|------------------------------------------------------------|
| AI Scientist           | end-to-end ML research automation          | general-purpose problem; human gate; ledger                |
| LangGraph              | long-running agent orchestration           | hypothesis-first decision before orchestration              |
| MLflow                 | execution tracking after the fact          | pre-experiment ranking and post-experiment interpretation   |
| DVC                    | data + pipeline versioning                 | hypothesis + risk + falsification metadata                 |
| Optuna                 | hyperparameter search                      | multi-criteria ranking with risk and reversibility         |
| Nextmv                 | DecisionOps for already-modelled decisions | upstream: "what is worth deciding in the first place?"      |
| Heatseeker             | real-world product market testing          | offline-first; cheaper; composable with their results      |
| Maxim AI               | agent evaluation                           | composable: their eval results become `evidence_against`    |

## The wedge

A `hypo` CLI that runs on every pull request:

```yaml
# .github/workflows/hypo-gate.yml
on: pull_request
jobs:
  hypo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e .
      - run: hypo init --objective "$TITLE" --output problem.json
      - run: hypo resolve -i problem.json --execute --ledger ledger.json
      - run: hypo promote -i ledger.json --output recommendation.json
      - uses: actions/upload-artifact@v4
        with:
          name: hypo-report
          path: report.json
```

The PR comment then shows the top-ranked hypothesis, the AXIS-8
score, the CVaR of the worst 10% of outcomes, the decision
(`TEST_NEXT` / `HOLD` / `HUMAN_REVIEW`), and the next-test contract.

The value is **daily, observable, and audit-friendly**.

## Why this wins

- **Daily utility**: every PR is a candidate problem.
- **Auditable**: the ledger is part of the PR.
- **Composable**: does not require replacing MLflow, DVC, or LangGraph.
- **Honest**: says `HOLD` and `HUMAN_REVIEW` instead of `definitely yes`.
- **Open source**: Apache 2.0; build on it.

## What we are NOT doing

- We are not building a hosted LLM service.
- We are not promising to "solve any problem".
- We are not competing with the experiment trackers — we sit *above*
  them in the decision stack.
