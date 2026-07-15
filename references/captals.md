# Captals: the continuity allocator

Captals is the system's continuity allocator. It is **not** a public currency and is **not** a price. It is the mechanism by which the organism decides who contributed verifiable work, in what proportion, and with what proof.

## Three (or four) layers, separated

| Layer       | Purpose                                                    | Mutability    |
|-------------|------------------------------------------------------------|---------------|
| MNB         | Causal, informational. Origin, context, identity.          | Not an asset  |
| Mem-bit     | Certificate and proof of a passage.                        | Sometimes transferable |
| M-bit       | Calculated contribution vector.                           | Internal      |
| CAPT        | Optional public unit of the eventual DAO.                 | HOLD (legal)  |
| LCU         | LLM Compute Unit — resource accounting.                    | Not transferable |

The canonical order is:

```
MNB → transformation → evidence → Mem-bit → admissibility → M-bit → CAPT
```

Never: `payment → truth`. Always: `evidence validated → value admissible`.

## M-bit geometric score

A M-bit has six positive dimensions. The score is the geometric mean times (1 - CVaR-like risk):

```
score = (Q * R * T * V * E * H)^(1/6) * (1 - risk)
```

If ANY positive dimension is zero, the score is **zero**. This prevents rewarding volume without utility.

## Proof chain

The proof chain has four kinds:

- **PoSE** — was the rule correctly applied?
- **PoCT** — was the causal transition between states valid?
- **PoTM** — did the artifact change nature while preserving causal identity?
- **PoLE** — was the evolutionary trajectory traceable?

A work is **complete** only when all four are attached.

## Reward function (proposed, not validated)

```
W_i = U_i * D_i * A_i * P_i
Reward_i = B_epoch * W_i / sum_j W_j
```

Where:

- `U_i` = utility (the M-bit geometric score)
- `D_i` = difficulty
- `A_i` = admissibility
- `P_i` = causal participation
- `B_epoch` = epoch budget (a finite pool, NOT infinite mint)

## Public issuance

Issuing CAPT as a public, transferable token requires:

- Independent legal review per jurisdiction
- A finalized tokenomics design
- Deployed smart contracts (WorkRegistry, ProofRegistry, ChallengeManager, CaptalsTreasury, CapabilityRegistry)
- An independent replay operator
- A blockchain witness

**Status**: HOLD on all public issuance. Internal M-bit and LCU are the only Captals-layer objects in production.
