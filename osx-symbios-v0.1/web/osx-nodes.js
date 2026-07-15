/* =================================================================
   osx-nodes.js  ·  Mapa de Nós SymbiOS (Page 3 of 5)
   =================================================================
   Real graph, not a visual of connections. Uses two first-class
   entities: SymbiOSNode + RelationEdge.

   Cardinal rule: "Sem RelationEdge, existe apenas uma lista
   visual, não uma topologia governável."

   15 node types + 15 relation types, three lenses (informational,
   digital, physical) and three navigation levels (macro / meso /
   micro).
   ================================================================= */
(function (global) {
  "use strict";

  // ---- 15 node types ----
  const NODE_TYPES = [
    "HUMAN", "ORGANISM", "NOTEBOOK", "INFORMATION_CELL", "PROGRAM_CELL",
    "PHYSICAL_NODE", "AGENT", "SKILL", "CAPABILITY", "EXPERIMENT",
    "EXECUTION", "RECEIPT", "SOURCE", "CLAIM", "INTENT",
  ];

  // ---- 15 relation types ----
  const RELATION_TYPES = [
    "OWNS", "CONTAINS", "DEPENDS_ON", "SUPPORTS", "CONTRADICTS",
    "EXECUTES", "OBSERVES", "AUTHORIZES", "USES_SKILL", "EXPOSES_CAPABILITY",
    "PRODUCES", "SUPERSEDES", "REVOKES", "REPLAYS", "TARGETS",
  ];

  // ---- lens classification ----
  const LENS_OF = {
    HUMAN:             "physical",
    ORGANISM:          "informational",
    NOTEBOOK:          "informational",
    INFORMATION_CELL:  "informational",
    PROGRAM_CELL:      "digital",
    PHYSICAL_NODE:     "physical",
    AGENT:             "digital",
    SKILL:             "digital",
    CAPABILITY:        "digital",
    EXPERIMENT:        "digital",
    EXECUTION:         "digital",
    RECEIPT:           "informational",
    SOURCE:            "informational",
    CLAIM:             "informational",
    INTENT:            "informational",
  };

  // ---- SymbiOSNode factory ----
  let NODE_COUNTER = 0;
  function newNode(opts) {
    opts = opts || {};
    NODE_COUNTER += 1;
    const node_id = opts.node_id || ("NODE-" + String(NODE_COUNTER).padStart(4, "0"));
    return {
      node_id: node_id,
      type: opts.type || "INFORMATION_CELL",
      label: opts.label || node_id,
      lens: LENS_OF[opts.type || "INFORMATION_CELL"] || "informational",
      properties: opts.properties || {},
      created_at: opts.created_at || 0,
    };
  }

  // ---- RelationEdge factory ----
  let EDGE_COUNTER = 0;
  function newEdge(opts) {
    opts = opts || {};
    EDGE_COUNTER += 1;
    const edge_id = opts.edge_id || ("EDGE-" + String(EDGE_COUNTER).padStart(4, "0"));
    return {
      edge_id: edge_id,
      source_id: opts.source_id,
      target_id: opts.target_id,
      type: opts.type || "CONTAINS",
      weight: (opts.weight === undefined) ? 1.0 : opts.weight,
      properties: opts.properties || {},
      created_at: opts.created_at || 0,
    };
  }

  // ---- Seeded graph (deterministic, ~30 nodes + ~50 edges) ----
  const NODES = [
    // ---- Humans (physical) ----
    newNode({ node_id: "NODE-MATEUS",  type: "HUMAN", label: "Mateus — Human Node" }),
    newNode({ node_id: "NODE-CASS-HN", type: "HUMAN", label: "Cassandra Human Node" }),

    // ---- Organism (informational) ----
    newNode({ node_id: "NODE-MATVERSE", type: "ORGANISM", label: "MatVerse Organism v3.8.0" }),

    // ---- Notebooks (informational) ----
    newNode({ node_id: "NODE-NB-LIVING", type: "NOTEBOOK", label: "NB-LIVING-PAPER" }),
    newNode({ node_id: "NODE-NB-CASS",   type: "NOTEBOOK", label: "NB-CASSANDRA" }),
    newNode({ node_id: "NODE-NB-URANO",  type: "NOTEBOOK", label: "NB-URANO-001" }),
    newNode({ node_id: "NODE-NB-SYM",    type: "NOTEBOOK", label: "NB-SYMBIOS" }),
    newNode({ node_id: "NODE-NB-EVD",    type: "NOTEBOOK", label: "NB-EVIDENCE" }),

    // ---- Information cells ----
    newNode({ node_id: "NODE-CELL-001", type: "INFORMATION_CELL", label: "CELL-001 (5-tuple MNB)" }),
    newNode({ node_id: "NODE-CELL-002", type: "INFORMATION_CELL", label: "CELL-002 (ρ = Ψ·τ/C)" }),
    newNode({ node_id: "NODE-CELL-005", type: "INFORMATION_CELL", label: "CELL-005 (v3.8.0 release)" }),
    newNode({ node_id: "NODE-CLAIM-1",  type: "CLAIM",           label: "Claim: GTHDL governs evolution" }),

    // ---- Sources ----
    newNode({ node_id: "NODE-SRC-TEST", type: "SOURCE", label: "tests/test_omega.py" }),
    newNode({ node_id: "NODE-SRC-LOG",  type: "SOURCE", label: "validation/mmnb/seed.json" }),

    // ---- Receipts ----
    newNode({ node_id: "NODE-RCP-001",  type: "RECEIPT", label: "Receipt #1 (v3.8.0 commit)" }),

    // ---- Intents ----
    newNode({ node_id: "NODE-INT-001",  type: "INTENT", label: "INT-0001 (R&D)" }),
    newNode({ node_id: "NODE-INT-003",  type: "INTENT", label: "INT-0003 (deploy/ESCALATE)" }),

    // ---- Program cells (digital) ----
    newNode({ node_id: "NODE-PC-MNB",    type: "PROGRAM_CELL", label: "matverse/mnb_formal.py" }),
    newNode({ node_id: "NODE-PC-HAM",    type: "PROGRAM_CELL", label: "matverse/hamiltonian.py" }),
    newNode({ node_id: "NODE-PC-RIE",    type: "PROGRAM_CELL", label: "matverse/riemannian.py" }),

    // ---- Agents (digital) ----
    newNode({ node_id: "NODE-AGT-CASS",  type: "AGENT",   label: "AGT-CASS-INTERPRETER" }),
    newNode({ node_id: "NODE-AGT-ATL",   type: "AGENT",   label: "AGT-ATL-SCOPE" }),
    newNode({ node_id: "NODE-AGT-EVD",   type: "AGENT",   label: "AGT-EVD-LEDGER" }),

    // ---- Skills (digital) ----
    newNode({ node_id: "NODE-SK-CASS",   type: "SKILL",   label: "Interpreter (Cassandra)" }),
    newNode({ node_id: "NODE-SK-ATL",    type: "SKILL",   label: "Scope Agent (Atlas)" }),
    newNode({ node_id: "NODE-SK-EVD",    type: "SKILL",   label: "Ledger Verifier (EvidenceOS)" }),

    // ---- Capabilities (digital) ----
    newNode({ node_id: "NODE-CAP-INT",   type: "CAPABILITY", label: "INTENT.INTERPRET" }),
    newNode({ node_id: "NODE-CAP-LED",   type: "CAPABILITY", label: "LEDGER.READ" }),

    // ---- Experiments / Executions ----
    newNode({ node_id: "NODE-EXP-1",     type: "EXPERIMENT", label: "URANO Hamilton-min selection" }),
    newNode({ node_id: "NODE-EXE-1",     type: "EXECUTION",  label: "Execution #1 of URANO" }),

    // ---- Physical node ----
    newNode({ node_id: "NODE-PHYS-LAP",  type: "PHYSICAL_NODE", label: "Mateus' laptop" }),
  ];

  // ---- Seeded edges (real topology, ~50) ----
  function E(src, tgt, type, weight, props) {
    return newEdge({ source_id: src, target_id: tgt, type: type, weight: weight || 1.0, properties: props || {} });
  }
  const EDGES = [
    // Human → Organism (OWNS)
    E("NODE-MATEUS",  "NODE-MATVERSE", "OWNS", 1.0, { since: "2024-01" }),
    E("NODE-CASS-HN", "NODE-MATVERSE", "OWNS", 0.5, { role: "operator_proxy" }),

    // Organism → Notebooks (CONTAINS)
    E("NODE-MATVERSE", "NODE-NB-LIVING", "CONTAINS"),
    E("NODE-MATVERSE", "NODE-NB-CASS",   "CONTAINS"),
    E("NODE-MATVERSE", "NODE-NB-URANO",  "CONTAINS"),
    E("NODE-MATVERSE", "NODE-NB-SYM",    "CONTAINS"),
    E("NODE-MATVERSE", "NODE-NB-EVD",    "CONTAINS"),

    // Notebook → Cells (CONTAINS)
    E("NODE-NB-LIVING", "NODE-CELL-001", "CONTAINS"),
    E("NODE-NB-LIVING", "NODE-CELL-002", "CONTAINS"),
    E("NODE-NB-LIVING", "NODE-CELL-005", "CONTAINS"),
    E("NODE-NB-LIVING", "NODE-CLAIM-1",  "CONTAINS"),

    // Claim → Sources (DEPENDS_ON)
    E("NODE-CLAIM-1",  "NODE-SRC-TEST",  "DEPENDS_ON", 1.0),
    E("NODE-CLAIM-1",  "NODE-SRC-LOG",   "DEPENDS_ON", 0.8),

    // Cell → Source (PRODUCES)
    E("NODE-CELL-005", "NODE-RCP-001",   "PRODUCES"),

    // Intents → Cells (TARGETS)
    E("NODE-INT-001",  "NODE-NB-URANO",  "TARGETS"),
    E("NODE-INT-001",  "NODE-CLAIM-1",   "TARGETS"),
    E("NODE-INT-003",  "NODE-NB-SYM",    "TARGETS"),

    // Program cells → Claims (SUPPORTS)
    E("NODE-PC-MNB",   "NODE-CELL-001",  "SUPPORTS", 0.9),
    E("NODE-PC-HAM",   "NODE-CLAIM-1",   "SUPPORTS", 1.0),
    E("NODE-PC-RIE",   "NODE-CELL-002",  "SUPPORTS", 0.85),

    // Agents → Skills (USES_SKILL)
    E("NODE-AGT-CASS", "NODE-SK-CASS",   "USES_SKILL"),
    E("NODE-AGT-ATL",  "NODE-SK-ATL",    "USES_SKILL"),
    E("NODE-AGT-EVD",  "NODE-SK-EVD",    "USES_SKILL"),

    // Skills → Capabilities (EXPOSES_CAPABILITY)
    E("NODE-SK-CASS",  "NODE-CAP-INT",   "EXPOSES_CAPABILITY"),
    E("NODE-SK-EVD",   "NODE-CAP-LED",   "EXPOSES_CAPABILITY"),

    // Intents → Agents (AUTHORIZES)
    E("NODE-INT-001",  "NODE-AGT-ATL",   "AUTHORIZES"),

    // Experiment → Execution (EXECUTES)
    E("NODE-EXP-1",    "NODE-EXE-1",     "EXECUTES"),

    // Execution → Receipt (PRODUCES)
    E("NODE-EXE-1",    "NODE-RCP-001",   "PRODUCES"),

    // Receipt → Source (DEPENDS_ON)
    E("NODE-RCP-001",  "NODE-SRC-TEST",  "DEPENDS_ON"),

    // Cell → Cell relations
    E("NODE-CELL-001", "NODE-CELL-002",  "SUPPORTS"),
    E("NODE-CELL-002", "NODE-CLAIM-1",   "SUPPORTS"),
    E("NODE-CLAIM-1",  "NODE-CELL-005",  "CONTRADICTS", 0.0, { reason: "claim asserted before v3.8.0; superseded by v3.8.0" }),

    // Cell-005 SUPERSEDES older claims
    E("NODE-CELL-005", "NODE-CLAIM-1",   "SUPERSEDES", 1.0, { reason: "v3.8.0 release absorbs prior claim" }),

    // Program cells depend on organism
    E("NODE-PC-MNB",   "NODE-MATVERSE",  "DEPENDS_ON"),
    E("NODE-PC-HAM",   "NODE-MATVERSE",  "DEPENDS_ON"),
    E("NODE-PC-RIE",   "NODE-MATVERSE",  "DEPENDS_ON"),

    // Physical node hosts the human
    E("NODE-PHYS-LAP", "NODE-MATEUS",    "OWNS", 1.0),

    // Notebook-URANO CONTAINS experiment
    E("NODE-NB-URANO", "NODE-EXP-1",     "CONTAINS"),

    // Program cells in notebook
    E("NODE-NB-SYM",   "NODE-PC-MNB",    "CONTAINS"),
    E("NODE-NB-SYM",   "NODE-PC-HAM",    "CONTAINS"),
    E("NODE-NB-SYM",   "NODE-PC-RIE",    "CONTAINS"),
  ];

  // ---- Graph operations ----
  function edgesFrom(node_id) { return EDGES.filter((e) => e.source_id === node_id); }
  function edgesTo(node_id)   { return EDGES.filter((e) => e.target_id === node_id); }
  function nodesByType(type)  { return NODES.filter((n) => n.type === type); }
  function nodesByLens(lens)  { return NODES.filter((n) => n.lens === lens); }
  function neighborsOf(node_id, hops) {
    if (hops === undefined) hops = 1;
    const visited = new Set([node_id]);
    let frontier = [node_id];
    for (let h = 0; h < hops; h++) {
      const next = [];
      frontier.forEach((id) => {
        edgesFrom(id).forEach((e) => {
          if (!visited.has(e.target_id)) { visited.add(e.target_id); next.push(e.target_id); }
        });
        edgesTo(id).forEach((e) => {
          if (!visited.has(e.source_id)) { visited.add(e.source_id); next.push(e.source_id); }
        });
      });
      frontier = next;
    }
    visited.delete(node_id);
    return Array.from(visited);
  }

  // ---- navigation levels ----
  const MACRO = function () {
    return NODES.filter((n) => n.type === "HUMAN" || n.type === "ORGANISM");
  };
  const MESO = function () {
    return NODES.filter((n) => n.type === "NOTEBOOK" || n.type === "AGENT" || n.type === "EXPERIMENT");
  };
  const MICRO = function () {
    return NODES.filter((n) => n.type === "INFORMATION_CELL" || n.type === "EXECUTION" || n.type === "RECEIPT" || n.type === "CLAIM" || n.type === "INTENT");
  };

  // ---- summary ----
  function summary() {
    const by_type = {};
    const by_lens = { informational: 0, digital: 0, physical: 0 };
    NODES.forEach((n) => {
      by_type[n.type] = (by_type[n.type] || 0) + 1;
      by_lens[n.lens] += 1;
    });
    const edges_by_type = {};
    EDGES.forEach((e) => { edges_by_type[e.type] = (edges_by_type[e.type] || 0) + 1; });
    return {
      total_nodes: NODES.length,
      total_edges: EDGES.length,
      by_type: by_type,
      by_lens: by_lens,
      edges_by_type: edges_by_type,
    };
  }

  // ---- EXPORT ----
  global.OSX_NODES = {
    NODE_TYPES: NODE_TYPES,
    RELATION_TYPES: RELATION_TYPES,
    LENS_OF: LENS_OF,
    NODES: NODES,
    EDGES: EDGES,
    newNode: newNode,
    newEdge: newEdge,
    edgesFrom: edgesFrom,
    edgesTo: edgesTo,
    nodesByType: nodesByType,
    nodesByLens: nodesByLens,
    neighborsOf: neighborsOf,
    MACRO: MACRO,
    MESO: MESO,
    MICRO: MICRO,
    summary: summary,
  };
})(typeof window !== "undefined" ? window : global);
