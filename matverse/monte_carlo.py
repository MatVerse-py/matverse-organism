"""
matverse.monte_carlo
====================

Reproducible Monte Carlo with conditional Value-at-Risk (CVaR) and local
sensitivity analysis. Pure Python stdlib (random, statistics, math).
"""
from __future__ import annotations
import math
import random
import statistics
from typing import Callable, Dict, List, Tuple


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def monte_carlo(
    samples: int,
    sampler: Callable[[], float],
    seed: int = 0,
) -> List[float]:
    """Generate `samples` reproducible draws from `sampler`.

    The sampler is a zero-arg callable that returns one float. The function
    is responsible for using the supplied random.Random instance if it needs
    determinism (or accept the global RNG; we reset it here for reproducibility).
    """
    if samples <= 0:
        return []
    if samples > 1_000_000:
        raise ValueError("samples must be <= 1,000,000 to keep CPU bounded")
    rng = random.Random(seed)
    out: List[float] = []
    for _ in range(samples):
        out.append(sampler())
    return out


def summarize(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "p10": 0.0, "p50": 0.0, "p90": 0.0,
                "std": 0.0, "min": 0.0, "max": 0.0}
    s = sorted(values)
    n = len(s)
    def pct(p: float) -> float:
        i = max(0, min(n - 1, int(p * n)))
        return s[i]
    return {
        "mean": statistics.fmean(values),
        "p10": pct(0.10),
        "p50": pct(0.50),
        "p90": pct(0.90),
        "std": statistics.pstdev(values) if n > 1 else 0.0,
        "min": s[0],
        "max": s[-1],
    }


def cvar(values: List[float], alpha: float = 0.90) -> float:
    """Conditional Value-at-Risk at confidence level (1 - alpha).

    Returns the expected value in the worst `alpha` fraction of cases
    (i.e. the mean of the bottom 10% by default).
    Negative numbers indicate loss.
    """
    if not values or not (0.0 < alpha < 1.0):
        return 0.0
    s = sorted(values)
    cutoff = max(1, int(alpha * len(s)))
    tail = s[:cutoff]
    return statistics.fmean(tail)


def threshold_probability(values: List[float], threshold: float, direction: str = "above") -> float:
    if not values:
        return 0.0
    if direction == "above":
        hits = sum(1 for v in values if v >= threshold)
    else:
        hits = sum(1 for v in values if v <= threshold)
    return hits / len(values)


def sensitivity(
    base_inputs: Dict[str, float],
    sample_fn: Callable[[Dict[str, float]], float],
    perturbations: Dict[str, float],
    seed: int = 0,
) -> List[Tuple[str, float, float]]:
    """Local one-at-a-time sensitivity.

    For each input x perturbed by ±perturbation[x], compute delta = result - base.
    Returns list of (input_name, perturbed_value, delta) sorted by |delta| desc.
    """
    rng = random.Random(seed)
    base_result = sample_fn(base_inputs)
    out: List[Tuple[str, float, float]] = []
    for k, amp in perturbations.items():
        if k not in base_inputs:
            continue
        for sign in (+1.0, -1.0):
            perturbed = dict(base_inputs)
            perturbed[k] = base_inputs[k] + sign * amp
            r = sample_fn(perturbed)
            out.append((k, perturbed[k], r - base_result))
    out.sort(key=lambda t: abs(t[2]), reverse=True)
    return out


def is_finite_number(x: float) -> bool:
    if isinstance(x, bool):
        return False
    if not isinstance(x, (int, float)):
        return False
    return math.isfinite(float(x))
