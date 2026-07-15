# ThermoCortex and the Eight Thermodynamic Laws

The ThermoCortex is the organ that turns energy, exergy, and carbon into first-class observables of the organism. It is governed by a constitutional layer of **eight thermodynamic laws**.

## The Eight Thermodynamic Laws

| ID  | Name                       | Statement                                                                     |
|-----|----------------------------|-------------------------------------------------------------------------------|
| L1  | Conservation               | No claim of net energy generation without identifying the source.              |
| L2  | Entropy is explicit        | Every execution produces heat, wear, noise, or availability loss; this MUST appear in the receipt. |
| L3  | Exergy > brute energy      | Not all kWh are equal. Quality is measured by exergy: `X = E * (1 - T0/T)`. |
| L4  | Useful work > compute vol  | More tokens, GPU, CPU time do not automatically mean more value.               |
| L5  | Residue is resource        | Heat, data, error, refuted hypotheses, idle capacity are recoverable resources. |
| L6  | No parasitism              | The organism must sustain itself without systematically externalizing environmental or social costs. |
| L7  | Vital reserve              | No activity may consume the resources required for continuity.                  |
| L8  | Independent proof         | No regenerative claim is admitted without independent measurement.              |

## Probes

A Probe is the contract that turns a workload description into a measurement.

```python
from matverse.probes import (
    DeclaredProbe, RaplProbe, NvmlProbe, CompositeProbe, make_default_probe
)
```

- **DeclaredProbe** — trusts caller-declared values; status `DECLARED`
- **RaplProbe** — reads Intel RAPL via `/sys/class/powercap/intel-rapl`; status `SENSOR` when available
- **NvmlProbe** — reads NVIDIA GPU power via `pynvml`; status `SENSOR` when available
- **CompositeProbe** — combines multiple probes; sums energy, max carbon
- **make_default_probe** — returns RAPL if available, else Declared

## Planetary Benefit Ratio (PBR)

```
PBR = (avoided + recovered + renewable + ecological) / (operational + embodied)
```

- `PBR < 1` → `NET_CONSUMER`
- `PBR = 1` → `THERMODYNAMIC_NEUTRAL_CANDIDATE`
- `PBR > 1` → `REGENERATIVE_CANDIDATE` (only with independent witness)

The Runner currently records everything with `measurement_status="DECLARED"` unless a real probe is wired in. To upgrade to SENSOR, instantiate `ThermoCortex(probe=RaplProbe())`.

## Receipt

```json
{
  "execution_id": "OP-...",
  "energy_wh": 0.5,
  "co2_g": 0.05,
  "exergy_wh": 0.4,
  "regenerative_ratio": 22.84,
  "planetary_benefit_ratio": 21.91,
  "measurement_status": "DECLARED",
  "ts": 1721000000
}
```

`regenerative_ratio` is `avoided / operational`. `planetary_benefit_ratio` is the full PBR formula. Both are first-class fields in the closure's `ThermoProjection`.
