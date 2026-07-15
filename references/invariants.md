# The Eight Invariants

Invariants are fail-closed constitutional conditions. Unlike Laws (which are versioned operational policies), invariants are conditions whose violation breaks identity, safety, or legitimacy. An invariant cannot be relaxed by a version bump; it can only be replaced by a new organism.

| ID  | Name                          | Statement                                                                     |
|-----|-------------------------------|-------------------------------------------------------------------------------|
| I1  | causal_identity               | No execution without causal identity (MMNB ancestry).                        |
| I2  | prohibited_action_blocked     | No prohibited action is ever authorized.                                     |
| I3  | proof_over_narrative          | No proof is replaced by a narrative.                                          |
| I4  | evidence_before_fact          | No hypothesis becomes fact without evidence.                                 |
| I5  | lineage_preserved             | No transformation erases its lineage.                                        |
| I6  | epistemic_economic_separation | No economic token buys epistemic validity.                                    |
| I7  | continuity_floor              | No operation may consume the resources required for organism continuity.      |
| I8  | planetary_boundary            | No claim of regenerative benefit is admitted without independent measurement. |

## Enforce

```python
from matverse.schema import Problem, Hypothesis
from matverse.invariants import Invariants, InvariantViolation

p = Problem(id="P", objective="x", scope="s", constraints=[],
            stakeholders=[], hypotheses=[
                Hypothesis(id="H", claim="c", variables={"v": 1.0},
                           evidence_for=["e"], evidence_against=["c"],
                           falsification_criteria="v < 0.5",
                           cost_estimate=1, expected_value=10, risk=0.2,
                           reversibility=0.9, lineage=["v3.0.0"]),
            ], metadata={"science_origin": "x", "contract": "y",
                         "ecosystem_impact": "z", "lineage": ["v3.0.0"]})

inv = Invariants()
verdicts = inv.evaluate(p)
# Returns a list of 8 InvariantVerdict.
# `inv.all_hold(verdicts)` is True iff all 8 hold.
# `inv.enforce(p)` raises InvariantViolation on the first violation.
```

## Invariant vs Law

| Aspect          | Invariant (I1..I8)                         | Law (L1..L8)                            |
|-----------------|--------------------------------------------|------------------------------------------|
| Mutability      | Cannot be relaxed by a version bump        | Versioned; can evolve                    |
| Violation       | System halts (`InvariantViolation`)        | Reported; missing is a development task |
| Examples        | "no execution without causal identity"     | "no claim without falsification"        |
| Implementation  | `matverse.invariants.Invariants`           | `matverse.laws.ConstitutionalLaws`       |

## The six organs that consume Invariants

- **Organism** — refuses to run a problem that fails I1, I2, I5
- **Closure Compiler** — refuses to emit CLOSED_FOR_DECLARED_SCOPE if any invariant fails
- **FullOrganismRunner** — passes InvariantVerdicts to the Cassandra reading and the closure canonization
- **Atlas** — flags organs with INVARIANT_VIOLATED status (via a future Apoptosis scheduler)
- **Publication layer** — refuses to set any platform status to anything other than PREPARED_NOT_PUBLISHED if a critical invariant is violated
- **MMNB** — refuses to write a new MMNB if its parent would create a lineage break (I5)
