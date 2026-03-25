# Arquitetura do Guardian

- `organism_client.py`: wrapper das APIs do kernel.
- `guardian_config.py`: configuração tipada e presets.
- `organism_guardian.py`: loop contínuo de health-check + ação.
- `run_guardian.sh`: launcher com verificação de dependência.
- `matverse-guardian.service`: unit file para execução persistente.
