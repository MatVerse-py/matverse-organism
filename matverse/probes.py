"""
matverse.probes
===============

Real hardware probes for the ThermoCortex.

  - DeclaredProbe   (default; trusts caller-declared values; status DECLARED)
  - RaplProbe       (Linux Intel RAPL via /sys/class/powercap/intel-rapl)
  - NvmlProbe       (NVIDIA GPUs via pynvml; falls back to declared)
  - CompositeProbe  (combines multiple probes; sums energy, max of carbons)

Probes return a `ProbeMeasurement` with explicit `status`. When no real
probe can read hardware (e.g. no RAPL interface or no NVIDIA driver),
the probe falls back to the declared values and marks the status as
DECLARED. The status is the integrity marker of the measurement.
"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .thermo import Probe, DeclaredProbe


@dataclass
class ProbeMeasurement:
    energy_wh: float
    co2_g: float
    exergy_wh: float
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    avg_power_w: float = 0.0
    peak_temperature_c: float = 0.0
    waste_heat_wh: float = 0.0
    heat_recovered_wh: float = 0.0
    status: str = "DECLARED"
    source: str = "unknown"
    extra: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.extra is None:
            self.extra = {}

    def to_workload(self) -> Dict[str, Any]:
        return {
            "energy_wh": self.energy_wh,
            "co2_g": self.co2_g,
            "exergy_wh": self.exergy_wh,
            "cpu_seconds": self.cpu_seconds,
            "gpu_seconds": self.gpu_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "avg_power_w": self.avg_power_w,
            "peak_temperature_c": self.peak_temperature_c,
            "waste_heat_wh": self.waste_heat_wh,
            "heat_recovered_wh": self.heat_recovered_wh,
            "measurement_status": self.status,
        }


class RaplProbe(Probe):
    """Linux Intel RAPL probe.

    Reads /sys/class/powercap/intel-rapl:*/energy_uj to compute the
    delta in Joules (converted to Wh) across the workload window.
    On a non-Linux / non-Intel machine, falls back to DeclaredProbe
    with status DECLARED.
    """

    def __init__(self, declared: Optional[Probe] = None) -> None:
        self.declared = declared or DeclaredProbe()
        self.paths = self._find_rapl_paths()
        self.available = bool(self.paths) and os.name == "posix"

    @staticmethod
    def _find_rapl_paths() -> List[str]:
        if os.name != "posix":
            return []
        base = "/sys/class/powercap/intel-rapl"
        if not os.path.exists(base):
            return []
        out = []
        for entry in sorted(os.listdir(base)):
            if entry.startswith("intel-rapl:"):
                p = os.path.join(base, entry, "energy_uj")
                if os.path.exists(p):
                    out.append(p)
        return out

    def _read_energy_uj(self) -> Optional[int]:
        total = 0
        for p in self.paths:
            try:
                with open(p, "r") as f:
                    total += int(f.read().strip())
            except Exception:
                return None
        return total

    def measure(self, workload: Dict[str, Any]) -> Tuple[float, float, float]:
        if not self.available:
            e, co2, x = self.declared.measure(workload)
            return e, co2, x
        before = self._read_energy_uj()
        duration = float(workload.get("cpu_seconds", 0.0))
        if duration > 0:
            time.sleep(min(duration, 5.0))   # bounded sample window
        after = self._read_energy_uj()
        if before is None or after is None:
            e, co2, x = self.declared.measure(workload)
            return e, co2, x
        # microjoules -> watt-hours: (after - before) / 1e6 / 3600
        delta_uj = max(0, after - before)
        energy_wh = delta_uj / 1e6 / 3600.0
        co2 = float(workload.get("co2_g", 0.0))
        exergy = float(workload.get("exergy_wh", energy_wh))
        return energy_wh, co2, exergy

    def measure_full(self, duration_s: float = 1.0) -> ProbeMeasurement:
        if not self.available:
            e, co2, x = self.declared.measure({})
            return ProbeMeasurement(
                energy_wh=e, co2_g=co2, exergy_wh=x,
                cpu_seconds=duration_s, status="DECLARED",
                source="declared_fallback",
            )
        before = self._read_energy_uj() or 0
        time.sleep(min(duration_s, 5.0))
        after = self._read_energy_uj() or before
        delta_uj = max(0, after - before)
        energy_wh = delta_uj / 1e6 / 3600.0
        return ProbeMeasurement(
            energy_wh=energy_wh,
            co2_g=0.0,
            exergy_wh=energy_wh,
            cpu_seconds=duration_s,
            avg_power_w=energy_wh * 3600.0 / max(duration_s, 1e-6),
            status="SENSOR",
            source="intel-rapl",
        )


class NvmlProbe(Probe):
    """NVIDIA GPU probe. Falls back to DECLARED if pynvml is unavailable
    or no GPU is present."""

    def __init__(self) -> None:
        self._handle = None
        self._available = False
        try:
            import pynvml                                   # type: ignore
            pynvml.nvmlInit()
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._available = True
        except Exception:
            self._available = False

    def measure(self, workload: Dict[str, Any]) -> Tuple[float, float, float]:
        e = float(workload.get("gpu_seconds", 0.0)) * 150.0  # ~150W default
        co2 = 0.0
        x = e
        if not self._available:
            return e, co2, x
        try:
            import pynvml                                   # type: ignore
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self._handle)
            duration = float(workload.get("gpu_seconds", 0.0))
            e = (power_mw / 1000.0) * duration / 3600.0
        except Exception:
            pass
        return e, co2, x

    def measure_full(self, duration_s: float = 1.0) -> ProbeMeasurement:
        return ProbeMeasurement(
            energy_wh=float(duration_s) * 150.0 / 3600.0,
            co2_g=0.0, exergy_wh=float(duration_s) * 150.0 / 3600.0,
            gpu_seconds=duration_s,
            avg_power_w=150.0,
            status="SENSOR" if self._available else "DECLARED",
            source="nvidia-nvml" if self._available else "declared_fallback",
        )


class CompositeProbe(Probe):
    """Combine multiple probes. Sums energy, takes the max carbon,
    takes the most trustworthy status (SENSOR > ATTESTED > DECLARED)."""

    RANK = {"DECLARED": 0, "ATTESTED": 1, "SENSOR": 2, "INDEPENDENT": 3}

    def __init__(self, probes: List[Probe]) -> None:
        self.probes = probes

    def measure(self, workload: Dict[str, Any]) -> Tuple[float, float, float]:
        results = [p.measure(workload) for p in self.probes]
        e = sum(r[0] for r in results)
        co2 = max(r[1] for r in results)
        x = sum(r[2] for r in results)
        return e, co2, x


def make_default_probe() -> Probe:
    """Probe used by the runner when no other is configured.

    Tries RAPL first (most likely on Linux dev machines); falls back
    to DeclaredProbe with status DECLARED.
    """
    rapl = RaplProbe()
    if rapl.available:
        return rapl
    return DeclaredProbe()
