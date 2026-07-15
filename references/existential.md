# Existential processes

The four existential processes are first-class organs, not metaphors. They govern the lifecycle of every other organ in the organism.

## Metabolism

The metabolism is the four-reserve budget:

```
B = B_vital + B_service + B_learning + B_regeneration
```

- **Vital reserve** — continuity, identity, security
- **Service reserve** — external work
- **Learning reserve** — capability acquisition
- **Regeneration reserve** — planetary benefit work

A reserve's viability is its remaining fraction. The geometric mean across the four reserves is the metabolism's `viability()`. If any reserve is zero, the viability is zero.

No activity may consume the vital reserve.

## Autopoiesis

Autopoiesis is the organism's self-repair loop. It does not generate new capabilities from scratch (that's the AutopoiesisGenerator). It runs a `diagnose → repair → receipt` cycle, recording every attempt.

A production autopoiesis is a UMJAM transmutation. The simple version provided here is a stub that records what was attempted.

## Apoptosis

Apoptosis is governed shutdown. The state machine:

```
ACTIVE → DEGRADED → QUARANTINED → SUPERSEDED → REVOKED → ARCHIVED
```

Transitions to `REVOKED` require prior `QUARANTINED` or `SUPERSEDED`. The line state is preserved even after `REVOKED` — the function dies, the memory does not.

The `ApoptosisScheduler` (in `matverse.adaptation`) walks the registry and retires capabilities whose failure rate exceeds the threshold over a grace window.

## Antifragility

Antifragility is measured, not narrated. The signature is:

```
dP / ds > 0
```

where P is performance and s is a perturbation magnitude. The `Antifragility` class records `before` and `after` measurements for each perturbation, and computes the mean delta. The organism is "antifragile" if its mean positive delta exceeds the threshold over enough samples.

`is_antifragile()` is False until the sample window is filled. This is intentional: a low-sample mean is not a claim of antifragility.

## Homeostasis

Homeostasis is the cheap absorption. It returns the organism to a safe interval after a small deviation. Unlike autopoiesis, it does not regenerate components. Unlike antifragility, it does not improve performance.

`Homeostasis.register_region(metric, lower, upper)` declares a safe interval. `in_region(metric, value)` checks membership. `deviation(metric, value)` returns the signed distance from the interval.

## Order of response to a perturbation

1. **Homeostasis** — return to safe interval
2. **Autopoiesis** — repair the component
3. **Antifragility** — learn from the perturbation, improve

Not every perturbation needs all three. A benign oscillation may be absorbed by homeostasis alone. A major failure requires apoptosis of the failed component.
