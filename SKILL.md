# MatVerse Organism v3.8.0

> *Um sistema de engenharia de problemas que recebe uma questão complexa, estrutura hipóteses concorrentes, identifica o próximo teste de maior valor informacional e preserva todo o raciocínio em relatório verificável.*

[![version](https://img.shields.io/badge/version-3.6.0-blue.svg)]()
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)]()
[![license](https://img.shields.io/badge/license-Apache%202.0-green.svg)]()
[![dependencies](https://img.shields.io/badge/dependencies-stdlib--only-brightgreen.svg)]()

v3.6.0 is the **eight-plus-one** release. It wires together the canonical
anatomy: Hypothesis Field, Cassandra, UMJAM, SVCA, Atlas, ThermoCortex,
Captals, Closure Macro Compiler, and the existential organs
(Metabolism, Autopoiesis, Apoptosis, Antifragility, Homeostasis),
governed by 8 Invariants and 8 versioned Laws.

---

## O que é

O **MatVerse Organism v3.0.0** é o órgão cognitivo executável do ecossistema MatVerse.
Ele é um **Campo de Hipóteses com metabolismo experimental e metacórtex**:

```
Problema
   → hipóteses concorrentes
   → 8 Leis Constitucionais
   → 8 lentes AXIS-8
   → Monte Carlo + CVaR + sensibilidade
   → decisão fail-closed
   → URANO executa experimento em sandbox
   → Receipt + Ledger hash-encadeado
   → Metacortex aprende como aprende
```

Ele **não** promete resolver todo e qualquer problema. Promete o que é executável e verificável:

- Recebe um problema estruturado;
- Estrutura alternativas concorrentes;
- Aplica as 8 Leis Constitucionais (verificáveis, não mágicas);
- Aplica as 8 lentes AXIS-8 (truthmode, redteam, 80/20, ...);
- Estima risco, valor, reversibilidade via Monte Carlo + CVaR + sensibilidade local;
- Emite decisão fail-closed: `TEST_NEXT`, `HUMAN_REVIEW`, `HOLD`, `REFUTED_PRESERVED`;
- Compila o próximo experimento via URANO Metabolic Runtime;
- Observa o resultado e atualiza o Metacortex (nível 3 de aprendizagem).

## Quando usar

- Antes de tomar uma decisão de arquitetura reversível.
- Antes de priorizar uma feature em um roadmap.
- Para auditar se um conjunto de hipóteses está falsificável.
- Para gerar um histórico verificável (ledger) de decisões técnicas.
- Como gate epistemológico antes de efeitos externos.

## Quando NÃO usar

- Para gerar texto livre, copy ou arte (use um LLM).
- Para problemas sem variáveis quantificáveis ("este design é bonito").
- Para substituir experimentação real de domínio — Monte Carlo é prospectivo, não observacional.

## Instalação

```bash
git clone https://github.com/MatVerse-py/matverse-organism.git
cd matverse-organism
pip install -e .   # opcional: package metadata; ou use diretamente
```

A biblioteca usa **apenas a biblioteca padrão do Python** (>= 3.8). Não há dependências externas obrigatórias.

## CLI rápido

```bash
# 1) criar um problema de exemplo
python -m matverse init --objective "Adoção de CLI offline" --n-hypotheses 3

# 2) rodar o organismo
python -m matverse resolve -i examples/cli_adoption.json

# 3) rodar ciclo completo (organismo + URANO + closure)
python -m matverse resolve -i examples/cli_adoption.json --execute \
    -o validation/report.json --ledger validation/ledger.json

# 4) alimentar o Metacortex com um learning record
python -m matverse promote \
    --problem-class "CLI_adoption" \
    --strategy "concrete_first" \
    --lenses "TRUTHMODE,REDTEAM,80/20" \
    --outcome PASS --predicted 0.85 --observed 1.0 \
    -o validation/metacortex_recommendation.json
```

## API Python

```python
from matverse import (
    Organism, URANO, ClosureCompiler, Metacortex, Ledger,
    Problem, Hypothesis, LearningRecord,
)

problem = Problem(
    id="P1",
    objective="Adoção de CLI offline",
    scope="dev-tools",
    stakeholders=["developers"],
    hypotheses=[
        Hypothesis(
            id="H_OFFLINE",
            claim="CLI offline dobra downloads na primeira semana",
            variables={"adoption_uplift": 2.0},
            evidence_for=["no auth", "fast feedback"],
            evidence_against=["SaaS marketing"],
            falsification_criteria="adoption_uplift < 1.2",
            test_method="monte_carlo",
            cost_estimate=20.0, expected_value=500.0,
            risk=0.2, reversibility=0.95,
            lineage=["v2.0.0"],
        ),
    ],
    metadata={
        "science_origin": "Diffusion of Innovations (Rogers, 1962)",
        "contract": "schema/v3/problem.schema.json",
        "ecosystem_impact": "additive, non-breaking",
    },
)

ledger = Ledger(path="validation/ledger.json")
organism = Organism(ledger=ledger, n_mc=2000, seed=42)
urano = URANO(ledger=ledger)
closure = ClosureCompiler(organism, urano, ledger=ledger)

report = closure.run_full_cycle(problem, seed=42, auto_execute=True)
print(report.closed, report.decision)

# Metacortex — nível 3 de aprendizagem
meta = Metacortex(ledger=ledger)
meta.record(LearningRecord(
    timestamp=0, problem_class="CLI_adoption", strategy="concrete_first",
    lenses_used=["TRUTHMODE", "80/20"], monte_carlo_n=2000, seed=42,
    outcome=report.decision, time_to_decision_s=0.1,
    predicted_probability=0.85, observed_outcome_value=1.0,
))
print(meta.recommend("CLI_adoption").recommended_strategy)
```

## Arquitetura

| Órgão                | Módulo                  | Função                                                                  |
|----------------------|-------------------------|-------------------------------------------------------------------------|
| Campo de Hipóteses   | `matverse.organism`     | Classifica problema, aplica leis, AXIS-8, MC, decisão fail-closed       |
| Metabolismo          | `matverse.urano`        | Compila hipóteses em contratos de experimento executáveis               |
| Fechamento           | `matverse.closure`      | Verifica que um ciclo completo (investigate→compile→run) foi cumprido   |
| Metacortex           | `matverse.metacortex`   | Agrega learning records, recomenda métodos por classe (nível 3)        |
| Ledger               | `matverse.ledger`       | Append-only, hash-chained, verificável                                  |
| Leis                 | `matverse.laws`         | 8 Leis Constitucionais (lineage, gates, fail-closed)                    |
| AXIS-8               | `matverse.axis8`        | 8 lentes analíticas                                                     |
| Monte Carlo          | `matverse.monte_carlo`  | MC determinístico, CVaR, sensibilidade local                           |
| Schema               | `matverse.schema`       | Data classes canônicas (Problem, Hypothesis, Experiment, LearningRecord)|

## Validação executada

```
Compilação Python:          PASS
Testes automatizados:       46/46 PASS
Execução do exemplo:        PASS (decision=HOLD, closure=closed)
Monte Carlo determinístico: PASS (seed=42 reproduzível)
NaN / infinito:             REJECTED
Ledger hash-encadeado:      PASS
Detecção de adulteração:    PASS
Validação externa:          NOT_PERFORMED
```

## Limites explícitos

- Hipóteses puramente qualitativas ("o design é elegante") **não** viram teste. Requerem tradução para variáveis numéricas.
- Monte Carlo é prospectivo. Não substitui dados observacionais do mundo real.
- O ledger prova **integridade local**, não verdade factual nem validação científica externa.
- O Metacortex aprende com observação real. Sem volume, sem confiança.

## Roadmap (próximas versões)

- v3.1.0 — Integração GitHub Action: `hypo` roda em PR e bloqueia merge se hipóteses críticas não forem falsificáveis.
- v3.2.0 — Emissor OpenLineage + atestado in-toto para interoperabilidade.
- v3.3.0 — Capability Registry plugável (LangGraph, MLflow, DVC como executores).
- v3.4.0 — Mode "Hypothesis Gate" para revisão de PRs com comentário SARIF.

## Linha evolutiva

A versão anterior (v2.0.0) está preservada em `lineage/v2.0.0/`. Nada foi apagado.
O organismo mantém a história da própria evolução como parte de sua governança.

## Citação

Ver `CITATION.cff` (Zenodo / GitHub-native).

## Licença

Apache License 2.0. Ver `LICENSE`.
