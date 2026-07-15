# MatVerse OSX + SymbiOS Network Notebook · v0.1

A **self-contained**, **offline**, single-folder web app that implements the
canonical MatVerse OSX interface (the "Living Paper Interface") and the
SymbiOS Network Notebook (the spatial, three-lens view of the organism).

No CDN, no external fonts, no analytics, no remote APIs. The whole app
runs from `file://` or from any static HTTP server.

## What is in v0.1

- **Constellation view** — a graph of the 6 primary nodes (OSX, SymbiOS,
  Cassandra, URANO, Atlas, Organism) and the 3 constitutional-physics
  objects (GTHDL, Riemannian, Epistemic). The MatVerse hub is at the
  center. Three orbital rings mark the three planes
  (Informational / Digital / Physical).
- **Notebook view** — a spatial notebook with 6 pre-seeded notebooks
  (Living Paper, Cassandra Copilot, URANO Laboratory, SymbiOS Network,
  Atlas Registry, Evidence Pack). Each cell is rendered with its
  epistemic state (HYP / EVD / ADM / CON / ESC). Selecting a cell
  shows the **triadic inspector** — the same cell, three lenses:
  - INFORMATIONAL — claim, sources, lineage, epistemic state
  - DIGITAL — program binding, runtime, permissions
  - PHYSICAL — physical node, operator, telemetry status
- **Figure Lab** — a deterministic SVG renderer for 7 of the 14
  canonical figure categories (FREE_BODY_DIAGRAM, PLOT_2D,
  FLOWCHART, NETWORK_GRAPH, CONCEPT_MAP, TIMELINE,
  SYSTEM_ARCHITECTURE) plus a fallback for the others. Has a Visual
  Ω-Gate with 5 structural checks.
- **Cognitive Canvas** — a pan/zoom SVG node editor with 7 node
  shapes (circle / diamond / hexagon / rect / rect-bold / circle-bold /
  diamond-blink) mapped to the 8 epistemic states, with connect /
  delete / export-JSON / import-JSON tools.
- **Atlas** — the constitutional registry: 12 organs + 3 physics +
  8 invariants + the operational law ("Constituição não executa…
  Witness não cria verdade.").
- **Registry** — a tabular view of all public organs and external
  holds (Sepolia anchor, Independent replay, Captals public token).
- **Organism runtime** — a one-button in-browser demo of the
  FullOrganismRunner that runs the canonical v3.8.0 cycle on a
  problem of your choice and prints the per-step trace.

## Architecture mirror

This v0.1 mirrors the v3.8.0 Python package
`matverse-organism`. Every constitutional organ from the Python
package has a corresponding tab / panel here:

| Python module (v3.8.0)        | OSX tab          |
|-------------------------------|------------------|
| `matverse.mnb_formal`         | Organism + Atlas |
| `matverse.hamiltonian`        | Atlas (physics)  |
| `matverse.riemannian`         | Atlas (physics)  |
| `matverse.epistemic`          | Cognitive Canvas |
| `matverse.omega`              | Top bar Ω value  |
| `matverse.canonical`          | Atlas (taxonomy) |
| `matverse.organism`           | Organism runtime |
| `matverse.atlas`              | Atlas            |
| `matverse.captals`            | Registry         |
| `matverse.probes`             | Organism (RAPL refs) |

## How to run

### Option 1 — open the file directly

```bash
# macOS
open index.html
# Linux
xdg-open index.html
# or just double-click index.html
```

### Option 2 — local HTTP server (recommended)

```bash
cd web
python3 -m http.server 8765
# then open http://localhost:8765
```

### Option 3 — run the smoke test

```bash
cd tests
node smoke.js
```

## Validation status

```
Smoke:  29/29 PASS
Render: 7/14 figure categories deterministic
Files:  6 (HTML + CSS + 4 JS), pure stdlib, no deps
Size:   ~80 KB
```

## Out of scope (HOLD)

- Multiple notebooks per page (v0.1 is one notebook at a time)
- Real network sync (v0.1 is single-user, offline)
- Server-side rendering (everything is client-side)
- The other 7 figure categories (MOLECULE, CELL, CYCLE, CIRCUIT,
  GEOMETRY, QUANTUM_CIRCUIT, INFOGRAPHIC) — fallback renderer only
- Authentication, accounts, persistence to disk (in-memory only)

## Constitutional position

Same as `matverse-organism` v3.8.0:

- The organism **prepares** (renders, computes, stores)
- The operator **signs** (decides what to commit, publish, release)
- The world **witnesses** (records, mirrors, attests)

All 4 platform publications remain `PREPARED_NOT_PUBLISHED` by design.
