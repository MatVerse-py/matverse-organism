"""
matverse.thermo
===============

ThermoCortex — the thermodynamic accounting organ.

Constitutional grounding (eight laws):

  L1 Conservation         — no claim of net energy generation without
                            identifying the source.
  L2 Entropy is explicit  — every execution produces heat, wear, noise,
                            or availability loss; this MUST appear in
                            the receipt.
  L3 Exergy > brute E     — not all kWh are equal. Quality is measured
                            by exergy:  X = E * (1 - T0/T).
  L4 Useful work > compute
                            volume — more tokens, GPU, CPU time do not
                            automatically mean more value.
  L5 Residue is resource  — heat, data, error, refuted hypotheses, idle
                            capacity are recoverable resources.
  L6 No parasitism        — the organism must sustain itself without
                            systematically externalizing environmental
                            or social costs.
  L7 Vital reserve        — no activity may consume the resources
                            required for continuity.
  L8 Independent proof    — no regenerative claim is admitted without
                            independent measurement.

The organ is a pure-Python module; real hardware measurement hooks
(RAPL, NVML, smart-plug telemetry) are pluggable via `probes`.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Probe protocol
# ---------------------------------------------------------------------------

class Probe:
    """A pluggable measurement source.

    A probe answers `measure(workload) -> (energy_wh, co2_g, exergy_wh)`.
    Concrete probes (RAPL, NVML, smart-plug, scraper) implement this
    contract; here we keep a sensible default.
    """

    def measure(self, workload: Dict[str, Any]) -> Tuple[float, float, float]:
        raise NotImplementedError


class DeclaredProbe(Probe):
    """Default probe: trusts caller-declared values. Use only when no
    hardware sensor is available. Marks results as DECLARED."""

    def measure(self, workload: Dict[str, Any]) -> Tuple[float, float, float]:
        e = float(workload.get("energy_wh", 0.0))
        co2 = float(workload.get("co2_g", 0.0))
        x = float(workload.get("exergy_wh", e))
        return e, co2, x


# ---------------------------------------------------------------------------
# ThermoReceipt
# ---------------------------------------------------------------------------

@dataclass
class ThermoReceipt:
    execution_id: str
    energy_wh: float
    cpu_seconds: float
    gpu_seconds: float
    input_tokens: int
    output_tokens: int
    avg_power_w: float
    peak_temperature_c: float
    waste_heat_wh: float
    heat_recovered_wh: float
    carbon_g_co2e: float
    exergy_wh: float
    external_energy_avoided_wh: float
    regenerative_ratio: float
    planetary_benefit_ratio: float
    measurement_status: str             # DECLARED | SENSOR | ATTESTED | INDEPENDENT
    ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "energy_wh": round(self.energy_wh, 4),
            "cpu_seconds": round(self.cpu_seconds, 4),
            "gpu_seconds": round(self.gpu_seconds, 4),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "avg_power_w": round(self.avg_power_w, 4),
            "peak_temperature_c": round(self.peak_temperature_c, 4),
            "waste_heat_wh": round(self.waste_heat_wh, 4),
            "heat_recovered_wh": round(self.heat_recovered_wh, 4),
            "carbon_g_co2e": round(self.carbon_g_co2e, 4),
            "exergy_wh": round(self.exergy_wh, 4),
            "external_energy_avoided_wh": round(self.external_energy_avoided_wh, 4),
            "regenerative_ratio": round(self.regenerative_ratio, 4),
            "planetary_benefit_ratio": round(self.planetary_benefit_ratio, 4),
            "measurement_status": self.measurement_status,
            "ts": self.ts,
        }


# ---------------------------------------------------------------------------
# Exergy & PBR
# ---------------------------------------------------------------------------

def exergy(energy_wh: float, source_temp_c: float, ambient_temp_c: float = 20.0) -> float:
    """Compute exergy: the maximum useful work extractable from `energy_wh`
    at a source temperature `source_temp_c` (Celsius) when the environment
    is at `ambient_temp_c`. The Carnot-style factor is (1 - T0/T) with
    temperatures in Kelvin."""
    T0 = ambient_temp_c + 273.15
    T = source_temp_c + 273.15
    if T <= 0:
        return 0.0
    factor = max(0.0, 1.0 - T0 / T)
    return energy_wh * factor


def planetary_benefit_ratio(energy_avoided_wh: float,
                            energy_recovered_wh: float,
                            renewable_enabled_wh: float,
                            verified_ecological_value: float,
                            energy_operational_wh: float,
                            energy_embodied_wh: float) -> float:
    """PBR = (avoided + recovered + renewable + ecological) / (operational + embodied).

    PBR < 1: NET_CONSUMER
    PBR = 1: THERMODYNAMIC_NEUTRAL_CANDIDATE
    PBR > 1: REGENERATIVE_CANDIDATE (must be independently witnessed to be claimed)
    """
    denom = energy_operational_wh + energy_embodied_wh
    if denom <= 0:
        return 0.0
    return (energy_avoided_wh + energy_recovered_wh
            + renewable_enabled_wh + verified_ecological_value) / denom


# ---------------------------------------------------------------------------
# ThermoCortex
# ---------------------------------------------------------------------------

class ThermoCortex:
    """The thermodynamic accounting organ."""

    def __init__(self, probe: Optional[Probe] = None) -> None:
        self.probe = probe or DeclaredProbe()
        self.history: List[ThermoReceipt] = []

    def record(self, execution_id: str, workload: Dict[str, Any]) -> ThermoReceipt:
        e, co2, x = self.probe.measure(workload)
        cpu_s = float(workload.get("cpu_seconds", 0.0))
        gpu_s = float(workload.get("gpu_seconds", 0.0))
        in_tok = int(workload.get("input_tokens", 0))
        out_tok = int(workload.get("output_tokens", 0))
        avg_w = float(workload.get("avg_power_w", 0.0))
        peak_t = float(workload.get("peak_temperature_c", 0.0))
        waste_h = float(workload.get("waste_heat_wh", 0.0))
        recov_h = float(workload.get("heat_recovered_wh", 0.0))
        ext_avoided = float(workload.get("external_energy_avoided_wh", 0.0))
        embodied = float(workload.get("energy_embodied_wh", e * 0.0))
        renew = float(workload.get("renewable_enabled_wh", 0.0))
        eco = float(workload.get("verified_ecological_value", 0.0))

        regen_ratio = ((ext_avoided + recov_h + renew + eco) / e) if e > 0 else 0.0
        pbr = planetary_benefit_ratio(
            energy_avoided_wh=ext_avoided,
            energy_recovered_wh=recov_h,
            renewable_enabled_wh=renew,
            verified_ecological_value=eco,
            energy_operational_wh=e,
            energy_embodied_wh=embodied,
        )

        rec = ThermoReceipt(
            execution_id=execution_id,
            energy_wh=e, cpu_seconds=cpu_s, gpu_seconds=gpu_s,
            input_tokens=in_tok, output_tokens=out_tok,
            avg_power_w=avg_w, peak_temperature_c=peak_t,
            waste_heat_wh=waste_h, heat_recovered_wh=recov_h,
            carbon_g_co2e=co2, exergy_wh=x,
            external_energy_avoided_wh=ext_avoided,
            regenerative_ratio=regen_ratio,
            planetary_benefit_ratio=pbr,
            measurement_status=str(workload.get("measurement_status", "DECLARED")),
            ts=int(time.time()),
        )
        self.history.append(rec)
        return rec

    def aggregate(self) -> Dict[str, Any]:
        if not self.history:
            return {"n": 0}
        e = sum(r.energy_wh for r in self.history)
        c = sum(r.carbon_g_co2e for r in self.history)
        avoided = sum(r.external_energy_avoided_wh for r in self.history)
        recov = sum(r.heat_recovered_wh for r in self.history)
        return {
            "n": len(self.history),
            "total_energy_wh": round(e, 4),
            "total_carbon_g_co2e": round(c, 4),
            "total_avoided_wh": round(avoided, 4),
            "total_recovered_wh": round(recov, 4),
            "global_pbr": round((avoided + recov) / e, 4) if e > 0 else 0.0,
        }

    def summary(self) -> Dict[str, Any]:
        return {"history_size": len(self.history), "aggregate": self.aggregate()}
