# MatVerse Guardian

O Guardian é um daemon que monitora continuamente o organismo e aplica ações simples de recuperação.

## Rodando localmente

```bash
./run_guardian.sh --base-url http://localhost:8765 --check-interval 10
```

## Arquivos de saída

- `guardian.log`: log textual do ciclo
- `diagnostics.json`: histórico em JSON

## Modos

- **thriving**: aplica perturbação leve para testar resiliência.
- **healthy**: apenas monitora.
- **stressed**: pausa perturbações.
- **critical**: injeta células para recuperação.
