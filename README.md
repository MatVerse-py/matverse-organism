# MatVerse Organism

The integrative cognitive layer of the MatVerse ecosystem. A hypothesis
field + metabolic runtime + metacortex in a single Python package, with
Python-stdlib-only execution and hash-chained audit.

> *"Não construímos ainda o organismo universal concluído.
> Construímos seu primeiro órgão cognitivo executável:
> um Campo de Hipóteses que sabe receber problemas, preservar alternativas,
> calcular incerteza, escolher experimentos, bloquear promessas indevidas
> e registrar sua evolução."* — MatVerse Builder, 2026

## Quickstart

```bash
# Run the bundled example end-to-end
python -m matverse resolve -i examples/cli_adoption.json --execute \
    -o validation/report.json --ledger validation/ledger.json

# See the top-ranked hypothesis and decision
python -c "import json; r = json.load(open('validation/report.json')); print(r['organism_report']['decision'])"
```

## Documentation

- [SKILL.md](SKILL.md) — full contract, API, examples
- [CHANGELOG.md](CHANGELOG.md) — evolution history
- [CITATION.cff](CITATION.cff) — citation metadata
- [references/architecture.md](references/architecture.md) — 8+1 organs model
- [references/canonical_laws.md](references/canonical_laws.md) — the 8 constitutional laws
- [references/limits.md](references/limits.md) — what the organism cannot do
- [references/product_strategy.md](references/product_strategy.md) — HypothesisOps wedge
- [validation/](validation/) — example outputs and ledger
- [examples/](examples/) — sample problems
- [lineage/v2.0.0/](lineage/v2.0.0/) — preserved previous version (v2.0.0)

## What it is NOT

- Not an LLM. Not a chatbot. Not a code generator.
- Not a "solver of all problems". The classifier explicitly rejects
  prohibited, infeasible, undecidable, and out-of-scope problems.
- Not a substitute for domain experimentation. Monte Carlo is prospective,
  not observational.
- Not a replacement for MLflow / DVC / LangGraph — it composes with them.

## What it IS

- A **Campo de Hipóteses** with fail-closed decisions.
- A **Metabolic Runtime** (URANO) that compiles hypotheses into executable
  experiments under sandbox constraints.
- A **Closure Compiler** that verifies a complete cognitive cycle.
- A **Metacortex** that learns how the organism learns (level 3).
- A **Ledger** that proves local integrity via hash chaining.
- **Zero external dependencies** — pure Python stdlib (>= 3.8).

## Contributing

Issues and PRs are welcome via GitHub. The constitutional laws are not
bikesheddable; the AXIS-8 lenses are not removable; the ledger is
append-only by design.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Citation

```bibtex
@software{matverse_organism_v3_2026,
  title  = {MatVerse Organism v3.0.0: A Hypothesis Field, Metabolic Runtime, and Metacortex for Auditable Problem Engineering},
  author = {MatVerse Builder and contributors},
  year   = {2026},
  month  = jul,
  url    = {https://github.com/MatVerse-py/matverse-organism},
  version = {3.0.0}
}
```
