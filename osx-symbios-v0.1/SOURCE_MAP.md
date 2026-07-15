# SOURCE_MAP — what came from where

| OSX v0.1 module          | Source / inspiration                                  | What it implements |
|--------------------------|-------------------------------------------------------|--------------------|
| `osx-core.js`            | matverse-organism v3.8.0 (matverse.canonical, matverse.omega) | 12 organs + 3 physics + 8 invariants + Ω + 5-tuple MNB + registry |
| `osx-figure-lab.js`      | corpus (Cassandra Atlas Visual spec, SUBSTRATO)       | 7 deterministic SVG renderers (FREE_BODY, PLOT_2D, FLOWCHART, NETWORK_GRAPH, CONCEPT_MAP, TIMELINE, SYSTEM_ARCH) + Visual Ω-Gate |
| `osx-canvas.js`          | corpus (Cognitive Canvas) + v0.2 kernel EpistemicState | 7 node shapes mapped to 8 epistemic states + select / add / connect / delete / export-JSON / import-JSON |
| `osx-organism.js`        | matverse-organism v3.8.0 (FullOrganismRunner)         | in-browser mini-runner for the canonical v3.8.0 cycle (genesis MMNB → Cassandra → COG → invariants → UMJAM → SVCA → closure → thermo → Ω → new MMNB) |
| `osx-app.js`             | corpus (SymbiOS Network Notebook, OSX view)           | top bar, dock, view switching, notebook renderers, Cassandra command bar |
| `osx.css`                | corpus (3 planes: informational / digital / physical) | color tokens mirror the constitutional planes; view layout |
| `index.html`             | corpus (SymbiOS Network Notebook layout, OSX-like chrome) | semantic structure + accessibility |
| `tests/smoke.js`         | —                                                     | 29 assertions covering exports, renderers, organism demo |

## What is **NOT** from v3.8.0

- The Cognitive Canvas shape glyphs (diamond-blink, etc.) — pure UX,
  inspired by the v0.2 kernel's EpistemicState enum.
- The constellation orbital rings — visual metaphor for the 3 planes.
- The Cassandra command bar regex routing — local rule-based, not LLM.

## What v0.1 does **not** do

- No machine learning
- No remote API calls
- No persistent storage (refresh = reset)
- No user accounts
- No multi-tab synchronization
- No blockchain
- No smart contracts
- No payment processing

## What v0.1 **does** do

- Render the constitutional surface (12+3+8)
- Run a deterministic organism cycle (in-browser)
- Produce figure-grade SVG
- Persist cognitive canvas state to JSON (download/upload)
- Recompute Ω on real inputs
- Show MMNB lineage cross-run
- Dispatch local rules from the Cassandra command bar

## Verification

- 29/29 smoke tests pass
- All 6 JS files parse without errors
- HTML validates against browser DOM (no console errors on load)
- The Organism runtime can be invoked from the Organism view
- The Figure Lab can be invoked from the Figure Lab view
- The Cognitive Canvas can be edited and the result exported

## Provenance

This v0.1 is the v3.8.0 organism's interface layer. It does not
replace the Python runtime; it makes the constitutional surface
visible and operable from a single self-contained folder.
