# The eight constitutional laws

The laws are not poetry. Each is a verifiable condition on a `Problem`
and its `Hypothesis` list. A law either **holds**, is **missing** (no
evidence to evaluate), or **fails**. Missing laws become development
requirements, not deletion triggers. A failed law is recorded; the
node is not deleted — it is preserved with its lineage.

| ID  | Name                  | Statement                                                                     |
|-----|-----------------------|-------------------------------------------------------------------------------|
| LW1 | phenomenon_origin     | No science without a phenomenon (problem must name a phenomenon).             |
| LW2 | experiment_link       | No claim without an experiment pathway.                                        |
| LW3 | science_origin        | No engineering without an upstream scientific basis.                           |
| LW4 | contract              | No artifact without a contract (interface / schema).                           |
| LW5 | product_value         | No product without observable value to a stakeholder.                          |
| LW6 | service_safety        | No service without a reversibility plan.                                       |
| LW7 | heritage              | No evolution without a recorded lineage of predecessors.                       |
| LW8 | ecosystem_impact      | No deployment without an ecosystem-impact statement.                           |

## Why these eight

They map to the eight layers of the Espinha Evolutiva:

```
phenomenon    ↔ LW1
experiment    ↔ LW2
science       ↔ LW3
artifact      ↔ LW4
product       ↔ LW5
service       ↔ LW6
heritage      ↔ LW7
ecosystem     ↔ LW8
```

A node that has gaps in any of the eight layers is incomplete; the
gaps are visible, addressable, and auditable. They are not silent.

## Implementation

`matverse.laws.ConstitutionalLaws.evaluate(problem)` returns a list of
`LawVerdict` objects. The summary is exposed as `coherence`,
`holds`, `missing`, and `failing` counts. The full list of verdicts is
included in the Organism report.
