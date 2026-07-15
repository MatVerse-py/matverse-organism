# MatVerse Organism — Operator Manual

This is the operator's guide to running the MatVerse Organism locally,
auditing a closure, and proposing a constitutional upgrade.

## 1. Quickstart

```bash
# Install (editable; pure Python stdlib, no external deps)
git clone https://github.com/MatVerse-py/matverse-organism.git
cd matverse-organism
pip install -e .

# Verify
python -m unittest discover -s tests
```

Expected: `Ran 146 tests in ... OK`.

## 2. The CLI

The `hypo` command is the public surface of the organism.

```bash
hypo --version
# hypo 3.7.0

# Create a problem from text
hypo init --objective "Should we adopt an offline CLI?" \
    --n-hypotheses 3 --output my-problem.json

# Run the Organism only (no transmutation)
hypo resolve -i my-problem.json --n-mc 1000

# Run the FULL organism (Field + UMJAM + SVCA + Closure)
hypo organism run -i my-problem.json -o closure.json

# Audit a closure's thermodynamic balance
hypo thermo record -i workload.json --execution-id EX1
hypo thermo report

# Read the live atlas
hypo atlas health

# MMNB causal memory
hypo mmnb show --store ./validation/mmnb
hypo mmnb lineage --store ./validation/mmnb
```

Run `hypo --help` for the full list of subcommands.

## 3. Auditing a closure

A closure is the canonical record of one cycle. To audit it:

```python
import json
from matverse.ledger import Ledger
from matverse.organism import Organism
from matverse.invariants import Invariants
from matverse.thermo import ThermoCortex

with open("closure.json") as f:
    closure = json.load(f)

# 1. Verify the ledger
ledger = Ledger(path="validation/ledger.json")
ledger.load()
print("Ledger:", ledger.verify())

# 2. Check the 8 invariants against the original problem
problem = closure["organism_report"]
# (you would re-construct Problem from the problem input)
# inv = Invariants()
# inv.evaluate(problem)

# 3. Check thermodynamic measurements
for receipt in closure["thermo"]["history"]:
    if receipt["measurement_status"] != "SENSOR":
        print(f"WARNING: {receipt['execution_id']} is {receipt['measurement_status']}, not SENSOR")
```

## 4. Proposing an upgrade

The organism's constitutional layer is not editable from the CLI.
Upgrades go through a multi-step process:

### 4a. Propose a new law version

The Laws are versioned. A new version of a law is proposed by:

1. Adding a new entry to `matverse.laws.ConstitutionalLaws` with a new ID (e.g. `LW1_v2`).
2. Adding tests for the new version in `tests/test_laws.py`.
3. Submitting a PR titled "LAW UPGRADE: LW1_v2".

### 4b. Propose a new capability

A new capability is added via the `CapabilityRegistry`:

```python
from matverse.capability import CapabilityRegistry, CapabilityContract

reg = CapabilityRegistry()
contract = CapabilityContract(
    id="my_capability.v1",
    name="My Capability",
    version="1.0.0",
    inputs={"x": "number"},
    outputs={"y": "number"},
    implementation=my_function,
    risk_level="LOW",
    tests=["test_my_capability"],
)
reg.register(contract)
```

A PR titled "CAPABILITY: my_capability.v1" is the canonical route.

### 4c. Propose a new invariant

Invariants cannot be relaxed by a version bump. Replacing an invariant
requires:

1. A new organism generation (e.g. v4.0.0).
2. Migration of every existing MMNB to the new invariant set.
3. Re-validation of every existing closure.

This is the most expensive upgrade and is the only kind of constitutional
change. The PR title must be "INVARIANT CHANGE: <reason>".

## 5. Public publication

The publication layer prepares metadata for Zenodo, GitHub Release,
Hugging Face, and blockchain. It does NOT publish. Each platform
requires a human operator to:

### Zenodo

1. Visit https://zenodo.org/deposit/new
2. Upload the `paper.md`, `MANIFEST.json`, and `closure.json` from the
   closure directory.
3. Set the community to "matverse".
4. Click "Publish". The DOI is recorded in `CITATION.cff`.

### GitHub Release

1. Tag the commit: `git tag v3.7.0 <sha>`
2. Push the tag: `git push origin v3.7.0`
3. The release is auto-drafted from the closure's `paper.abstract`
   and `code.repository`.

### Hugging Face

1. Visit https://huggingface.co/new-dataset
2. Upload the `closure/` directory contents as a dataset.
3. Set the license to `apache-2.0`.

### Blockchain

1. Compute the Merkle root from the closure's `canonization.merkle_root`.
2. Call the `CaptalsTreasury.anchor(merkle_root)` contract on the
   target network.
3. Wait for `WITNESSED_EXTERNAL` state.

After all four, the closure advances from `REPLAYED_INDEPENDENT` to
`WITNESSED_EXTERNAL`. The `MMNB` chain records the witness as the
next `MMNB_t+1`.

## 6. Troubleshooting

### "I get 0 in `atlas_nodes`"

The Atlas is empty by default. The `FullOrganismRunner` seeds it with
the canonical organs at `__init__`. If you instantiate `Atlas()` directly,
you must call `register_organ()` and `register_capability()` yourself.

### "My MMNB chain has gaps"

The MMNB store writes a new MMNB at the end of every runner.run() call.
If you call `runner.run()` only once, you have one child. To build a
chain, call `run()` repeatedly with `mmnb_dir` pointing to a persistent
directory.

### "The thermo PBR is huge (e.g. 21.9)"

This is because the workload has `external_energy_avoided_wh=12.0` and
`energy_wh=0.5`. The PBR is `(12 + small) / 0.5 ≈ 24+`. With real RAPL
data, the PBR will be much smaller (often < 1, i.e. NET_CONSUMER).

The "21.9" is a synthetic example, not a measurement.

## 7. Support

The organism is open source under Apache 2.0. Issues and PRs go to
https://github.com/MatVerse-py/matverse-organism.
