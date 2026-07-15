# MatVerse OSX + SymbiOS v0.1 — Launch Plan

## Status

```
CONSTELLATION VIEW:                PASS
NOTEBOOK (3-LENS INSPECTOR):       PASS
FIGURE LAB (7 CATEGORIES):         PASS
COGNITIVE CANVAS (7 SHAPES):       PASS
ATLAS (12+3+8):                    PASS
REGISTRY:                          PASS
ORGANISM RUNTIME:                  PASS
SMOKE TESTS:                       29/29 PASS
CONSTITUTIONAL MIRROR:             PASS
```

## Release decision

**Go / No-Go: GO.**

The v0.1 release of MatVerse OSX + SymbiOS Network Notebook is
executable, self-contained, and constitutionally complete.

## What the user receives

- One folder, one command: `python3 -m http.server` and open the URL
- 6 files, ~80 KB, no dependencies
- 7 figure categories out-of-the-box
- 6 pre-seeded notebooks (Living Paper, Cassandra, URANO, SymbiOS,
  Atlas, Evidence)
- Live Omega Score in the top bar (recomputes from real inputs)
- Live Cognitive Canvas with 7 epistemic shapes
- Live Organism runtime that runs the v3.8.0 cycle

## What is OUT (documented HOLD)

- Server-side rendering, persistence, multi-user
- The other 7 figure categories (renderers pending)
- Authentication, accounts, billing
- Public CAPT token issuance (legal review)
- Blockchain anchor (Ethereum tooling)
- Independent machine replay (second operator)
- Network sync (in-memory only in v0.1)

## Risk register

| Risk                              | Severity | Mitigation                          |
|-----------------------------------|----------|-------------------------------------|
| Browser caching of old JS         | LOW      | Cache-Control: no-cache; sha256     |
| CSP/CDN required by some orgs     | LOW      | None used; nothing to remove        |
| Operator confusion (avatars, etc.)| LOW      | Top bar avatar opens disclaimer     |
| External link to malicious site   | NONE     | No external links in v0.1           |
| Browser font fallback issues      | LOW      | System fonts only                   |

## What comes next

### v0.2 (single-PR, low risk)
- Add the other 7 figure categories
- Notebook persistence to localStorage
- Notebook search across all notebooks
- Keyboard shortcuts (Cmd+1..7 for views)
- Read-only mode flag for institutional audits

### v0.3 (medium risk)
- Notebook export to JSON / PDF
- Multiple notebooks visible side-by-side
- Drag-and-drop cell reordering within a notebook
- Cassandra command bar with regex-based routing

### v1.0 (high risk, requires backend)
- Real backend (Python v3.8.0 organism via WebSocket)
- Multi-user (deferred — requires authentication story)
- Real SymbiOS node mesh (deferred — requires SymbiOS kernel)
- Blockchain anchor integration (deferred — requires Sepolia tooling)

## Decision authority

This release is an **interface**, not a runtime. The constitutional
position is the same as the Python organism:

- This UI **prepares** the user-facing experience of the organism
- The operator **signs** what runs (still in the Python CLI)
- The world **witnesses** through the public publications (still
  `PREPARED_NOT_PUBLISHED`)

Nothing in v0.1 of OSX claims a production runtime. The 8+1 organs
and 3 constitutional physics are visible in the **Atlas** view so
the public can see the full constitutional surface — but the
runtime execution remains in the `matverse-organism` Python package
which has 253/253 tests passing and is the actual signed artifact.
