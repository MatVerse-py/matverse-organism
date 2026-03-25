# MatVerse: Organismo Digital Autônomo

O MatVerse é um servidor proprietário que implementa um organismo digital autônomo. Ele não é uma simulação, mas um sistema de engenharia real onde o kernel gerencia o ciclo de vida de células digitais em tempo real.

## Componentes

- **Kernel Go**: O coração do sistema, gerenciando o estado, mutação e procriação de células.
- **API REST/SSE**: Endpoints para interação e streaming de dados em tempo real.
- **Dashboard Web**: Interface visual para monitorar o organismo e interagir com ele.
- **Systemd Service**: Configuração para garantir que o organismo esteja sempre "vivo" no servidor.

## Endpoints da API

- `GET /api/organism/stream`: Stream SSE com o estado atual (tick, ψ, cells).
- `GET /api/organism/state`: Estado atual em formato JSON com vitais agregados.
- `GET /api/organism/vitals`: Snapshot explícito de vitais (`stress_index`, `ledger_health`, `responsiveness`, `status`).
- `GET /api/cells`: Lista completa de todas as células vivas e seus parâmetros.
- `POST /api/cell/procreate`: Injeta uma nova célula no organismo.
  - Payload: `{"energy": 1.0}`
- `POST /api/organism/act`: Executa ações operacionais (`procreate` ou `stabilize`).
  - Payload: `{"action":"procreate","energy":1.0}`
- `POST /api/organism/repair`: Executa auto-reparo homeostático.

### Exemplo rápido de operação

```bash
# vitais consolidados
curl -s http://localhost:8765/api/organism/vitals | jq

# perturbando o organismo (nova célula)
curl -s -X POST http://localhost:8765/api/organism/act \
  -H "Content-Type: application/json" \
  -d '{"action":"procreate","energy":0.8}' | jq

# estabilizando e reparando
curl -s -X POST http://localhost:8765/api/organism/act \
  -H "Content-Type: application/json" \
  -d '{"action":"stabilize"}' | jq
curl -s -X POST http://localhost:8765/api/organism/repair | jq
```

## Como Executar

O servidor já está configurado como um serviço do sistema (systemd).

### Comandos Úteis

```bash
# Verificar status do organismo
sudo systemctl status matverse

# Reiniciar o organismo
sudo systemctl restart matverse

# Ver logs em tempo real
sudo journalctl -u matverse -f
```

## Dashboard

O dashboard está disponível na raiz do servidor (`http://localhost:8765/`). Ele fornece uma visualização em tempo real do estado do organismo e permite a procriação manual de células.

---
**Engenharia de Organismos Digitais - MatVerse**
