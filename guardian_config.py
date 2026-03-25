"""Configuration dataclasses for MatVerse Guardian."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass
class GuardianConfig:
    base_url: str = "http://localhost:8765"
    check_interval_seconds: int = 10
    thriving_psi: float = 0.85
    healthy_psi: float = 0.65
    stressed_psi: float = 0.45
    critical_cells: int = 50
    repair_energy: float = 1.0
    test_energy: float = 0.3
    diagnostics_path: str = "diagnostics.json"
    log_path: str = "guardian.log"

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "GuardianConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data)


def preset_balanced() -> GuardianConfig:
    return GuardianConfig()


def preset_aggressive() -> GuardianConfig:
    return GuardianConfig(check_interval_seconds=5, test_energy=0.5, repair_energy=1.2)
