# MatVerse: Organismo Digital Autônomo

O MatVerse é um servidor proprietário que implementa um organismo digital autônomo. Ele não é uma simulação, mas um sistema de engenharia real onde o kernel gerencia o ciclo de vida de células digitais em tempo real.

## Componentes

- **Kernel Go**: O coração do sistema, gerenciando o estado, mutação e procriação de células.
- **API REST/SSE**: Endpoints para interação e streaming de dados em tempo real.
- **Dashboard Web**: Interface visual para monitorar o organismo e interagir com ele.
- **Systemd Service**: Configuração para garantir que o organismo esteja sempre "vivo" no servidor.
- **Guardian Python**: Agente contínuo para monitoramento de saúde, perturbação controlada e auto-recuperação.

## Endpoints da API

- `GET /api/organism/stream`: Stream SSE com o estado atual (tick, ψ, cells).
- `GET /api/organism/state`: Estado atual em formato JSON.
- `GET /api/cells`: Lista completa de todas as células vivas e seus parâmetros.
- `POST /api/cell/procreate`: Injeta uma nova célula no organismo.
  - Payload: `{"energy": 1.0}`

## Guardian Autômato

Arquivos principais:

- `organism_client.py`: cliente CLI para diagnóstico manual.
- `guardian_config.py`: configurações e presets do guardião.
- `organism_guardian.py`: daemon contínuo com health-check e ações automáticas.
- `run_guardian.sh`: launcher para execução local.
- `matverse-guardian.service`: unit file para deploy com systemd.

### Início rápido

```bash
python3 -m pip install requests
chmod +x run_guardian.sh
./run_guardian.sh --base-url http://localhost:8765 --check-interval 10
```

Em outro terminal:

```bash
python3 organism_client.py --state
python3 organism_client.py --stream 10
python3 organism_client.py --measure-response 0.7 --observation-seconds 5
```

### Documentação adicional

- `QUICKSTART.md`
- `GUARDIAN.md`
- `ARCHITECTURE.md`
- `MANIFEST.md`

## Como Executar

O servidor pode rodar como serviço systemd.

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
