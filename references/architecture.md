# Architecture: the eight-plus-one organs

The MatVerse Organism v3.0.0 is decomposed into nine functional organs
that compose a closed cognitive cycle. The decomposition is not
metaphorical — each organ is a Python module with a single public
responsibility, and the cycle is enforced by the `ClosureCompiler`.

```
1. Membrane        matverse.schema          data contracts (Problem, Hypothesis, …)
2. Memory          matverse.ledger          hash-chained, append-only
3. Hypothesis      matverse.organism        Campo de Hipóteses
   field
4. Metabolism      matverse.urano           Hypothesis → ExperimentContract → Execution
5. Capabilities    matverse.organism (lens) + urano (executor registry)
6. Execution gate  matverse.closure         decide what to autorun, what to hold
7. Causal memory   matverse.ledger          receipts feed the chain
8. Evolution       matverse.metacortex      level-3 learning: method selection
9. Metacortex      matverse.metacortex      observer of the other eight
```

The cycle is:

```
Problem
  → schema (1)
    → organism.investigate  (3: laws + lenses + MC + decision)
      → urano.compile       (4: contract)
        → urano.run         (4: executor + receipt)
          → closure.run_full_cycle (6: verify cycle is closed)
            → ledger.append  (2 + 7: receipt in chain)
              → metacortex.record (8: learn from outcome)
```

The Metacortex (9) does not appear in the per-problem cycle; it
observes the cycle over many problems and only intervenes by
recommending a strategy on the next problem of the same class.

## State diagram for a single problem

```
NEW
  ↓ classify
OPEN_FOR_INVESTIGATION ─── investigate ───→ ranked + report
  ↓
  ├─ decision: TEST_NEXT          → compile → run → CLOSED
  ├─ decision: HOLD_ACTION        → CLOSED (no experiment run)
  ├─ decision: HUMAN_REVIEW       → CLOSED (awaiting human)
  ├─ decision: REFUTED_PRESERVED  → CLOSED (preserved for lineage)
  ├─ decision: PROHIBITED_ACTION  → CLOSED (hard gate)
  ├─ decision: OUT_OF_SCOPE       → CLOSED (hard gate)
  └─ decision: UNDECIDABLE_CANDIDATE → CLOSED (hard gate)
```

Every transition writes a receipt. Every receipt is hash-chained.
A failed verify() means somebody rewrote the chain.
