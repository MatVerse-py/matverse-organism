/* =================================================================
   osx-intent.js  ·  Gerenciador de Intenções (Page 1 of 5)
   =================================================================
   Entry point of the SymbiOS causal chain. Every human language
   command that enters the organism becomes an Intent here.

   Constitutional position: this page DOES NOT execute. It
   classifies, decomposes, routes, and ESCALATES when in doubt.
   Per the corpus: "Interpretação não decide sozinha."

   State machine: 12 states
     RECEIVED → CLASSIFIED → DECOMPOSED → ROUTED →
     WAITING_AUTHORIZATION → ACTIVE → COMPLETED
                       ↘ HOLD / BLOCK / ESCALATE
                                          ↘ FAILED / CANCELLED
   ================================================================= */
(function (global) {
  "use strict";

  // ---- 12 intent states (canonical, fail-closed) ----
  const INTENT_STATES = [
    "RECEIVED", "CLASSIFIED", "DECOMPOSED", "ROUTED",
    "WAITING_AUTHORIZATION", "ACTIVE", "HOLD", "BLOCK",
    "ESCALATE", "COMPLETED", "FAILED", "CANCELLED",
  ];

  // ---- 6 intent classes ----
  const INTENT_CLASSES = [
    "RESEARCH_AND_ENGINEERING",
    "OBSERVATION_AND_LEDGER",
    "EXECUTION_AND_DEPLOY",
    "PUBLICATION_AND_PROOF",
    "GOVERNANCE_AND_AUDIT",
    "REPLAY_AND_RECONCILIATION",
  ];

  // ---- valid transitions (12 → 12 → ...) ----
  const INTENT_TRANSITIONS = {
    RECEIVED:              ["CLASSIFIED", "BLOCK", "ESCALATE"],
    CLASSIFIED:            ["DECOMPOSED", "BLOCK", "ESCALATE"],
    DECOMPOSED:            ["ROUTED", "BLOCK", "ESCALATE"],
    ROUTED:                ["WAITING_AUTHORIZATION", "ACTIVE", "BLOCK", "ESCALATE"],
    WAITING_AUTHORIZATION: ["ACTIVE", "BLOCK", "CANCELLED", "ESCALATE"],
    ACTIVE:                ["COMPLETED", "FAILED", "CANCELLED", "HOLD", "ESCALATE"],
    HOLD:                  ["ACTIVE", "CANCELLED", "ESCALATE"],
    BLOCK:                 ["CANCELLED"],
    ESCALATE:              ["ACTIVE", "BLOCK", "CANCELLED"],
    COMPLETED:             [],   // terminal
    FAILED:                ["CANCELLED"], // terminal aside from cancel
    CANCELLED:             [],   // terminal
  };

  // ---- risk levels ----
  const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

  // ---- Intent factory ----
  let INTENT_COUNTER = 0;
  function newIntent(opts) {
    opts = opts || {};
    INTENT_COUNTER += 1;
    const intent_id = opts.intent_id || ("INT-" + String(INTENT_COUNTER).padStart(4, "0"));
    const intent = {
      intent_id: intent_id,
      human_node_id: opts.human_node_id || "HUMAN-MATEUS-001",
      statement: opts.statement || "",
      intent_class: opts.intent_class || "OBSERVATION_AND_LEDGER",
      target_notebook_id: opts.target_notebook_id || null,
      requested_capabilities: opts.requested_capabilities || [],
      risk: opts.risk || "LOW",
      external_effect: opts.external_effect === true,
      state: "RECEIVED",
      history: [{ state: "RECEIVED", at: 0 }],
      created_at: 0,
      metadata: opts.metadata || {},
    };
    return intent;
  }

  // ---- transition with audit ----
  function transition(intent, next_state, at) {
    if (at === undefined) at = 0;
    const allowed = INTENT_TRANSITIONS[intent.state] || [];
    if (allowed.indexOf(next_state) === -1) {
      return {
        ok: false,
        reason: "illegal_transition",
        from: intent.state,
        to: next_state,
        allowed: allowed,
      };
    }
    intent.state = next_state;
    intent.history.push({ state: next_state, at: at });
    return { ok: true, intent: intent };
  }

  // ---- decompose into subtasks (deterministic) ----
  function decompose(intent) {
    if (intent.intent_class === "EXECUTION_AND_DEPLOY" && intent.external_effect) {
      // fail-closed: execution with external effect must ESCALATE
      return {
        subtasks: [],
        routing: "ESCALATE",
        reason: "external_effect=True + EXECUTION_AND_DEPLOY → Ω-Gate required",
      };
    }
    if (intent.intent_class === "PUBLICATION_AND_PROOF") {
      return {
        subtasks: [
          { kind: "ledger.verify", target: "all_active_receipts" },
          { kind: "evidence.summarize", target: "evidence_packs" },
          { kind: "manifest.build", target: "publication_manifest" },
        ],
        routing: "WAITING_AUTHORIZATION",
        reason: "publication requires EvidenceOS manifest + operator signature",
      };
    }
    if (intent.intent_class === "RESEARCH_AND_ENGINEERING") {
      return {
        subtasks: [
          { kind: "atlas.deep_research", target: intent.target_notebook_id || "NB-MATVERSE" },
          { kind: "urano.run_experiment", target: intent.target_notebook_id || "NB-MATVERSE" },
          { kind: "evidence.collect", target: "experiment_results" },
        ],
        routing: "ROUTED",
        reason: "R&D decomposes into research + experiment + evidence collection",
      };
    }
    return {
      subtasks: [
        { kind: "atlas.observe", target: intent.target_notebook_id || "all" },
      ],
      routing: "ROUTED",
      reason: "default decomposition",
    };
  }

  // ---- seeded intents (deterministic fixtures) ----
  const SAMPLE_INTENTS = [
    {
      intent_id: "INT-0001",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Analise o corpus e construa um experimento",
      intent_class: "RESEARCH_AND_ENGINEERING",
      target_notebook_id: "NB-MATVERSE",
      requested_capabilities: ["atlas.deep_research", "urano.run_experiment"],
      risk: "MEDIUM",
      external_effect: false,
      state: "DECOMPOSED",
      history: [
        { state: "RECEIVED", at: 0 },
        { state: "CLASSIFIED", at: 1 },
        { state: "DECOMPOSED", at: 2 },
      ],
    },
    {
      intent_id: "INT-0002",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Publique v3.8.0 no Zenodo",
      intent_class: "PUBLICATION_AND_PROOF",
      target_notebook_id: "NB-EVIDENCE",
      requested_capabilities: ["evidence.summarize", "manifest.build", "zenodo.deposit"],
      risk: "HIGH",
      external_effect: true,
      state: "WAITING_AUTHORIZATION",
      history: [
        { state: "RECEIVED", at: 0 },
        { state: "CLASSIFIED", at: 1 },
        { state: "DECOMPOSED", at: 2 },
        { state: "ROUTED", at: 3 },
        { state: "WAITING_AUTHORIZATION", at: 4 },
      ],
    },
    {
      intent_id: "INT-0003",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Execute deploy do SymbiOS",
      intent_class: "EXECUTION_AND_DEPLOY",
      target_notebook_id: "NB-SYMBIOS",
      requested_capabilities: ["symbios.deploy"],
      risk: "CRITICAL",
      external_effect: true,
      state: "ESCALATE",
      history: [
        { state: "RECEIVED", at: 0 },
        { state: "CLASSIFIED", at: 1 },
        { state: "DECOMPOSED", at: 2 },
        { state: "ESCALATE", at: 3 },
      ],
    },
    {
      intent_id: "INT-0004",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Reproduza o replay do receipt 7",
      intent_class: "REPLAY_AND_RECONCILIATION",
      target_notebook_id: "NB-EVIDENCE",
      requested_capabilities: ["evidence.replay"],
      risk: "LOW",
      external_effect: false,
      state: "ACTIVE",
      history: [
        { state: "RECEIVED", at: 0 },
        { state: "CLASSIFIED", at: 1 },
        { state: "DECOMPOSED", at: 2 },
        { state: "ROUTED", at: 3 },
        { state: "ACTIVE", at: 4 },
      ],
    },
    {
      intent_id: "INT-0005",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Audite as decisões da semana",
      intent_class: "GOVERNANCE_AND_AUDIT",
      target_notebook_id: "NB-EVIDENCE",
      requested_capabilities: ["evidence.audit"],
      risk: "LOW",
      external_effect: false,
      state: "COMPLETED",
      history: [
        { state: "RECEIVED", at: 0 },
        { state: "CLASSIFIED", at: 1 },
        { state: "DECOMPOSED", at: 2 },
        { state: "ROUTED", at: 3 },
        { state: "ACTIVE", at: 4 },
        { state: "COMPLETED", at: 5 },
      ],
    },
    {
      intent_id: "INT-0006",
      human_node_id: "HUMAN-MATEUS-001",
      statement: "Liste as células do notebook URANO",
      intent_class: "OBSERVATION_AND_LEDGER",
      target_notebook_id: "NB-URANO-001",
      requested_capabilities: ["atlas.list_cells"],
      risk: "LOW",
      external_effect: false,
      state: "RECEIVED",
      history: [
        { state: "RECEIVED", at: 0 },
      ],
    },
  ];

  // ---- summary across intents ----
  function summary(intents) {
    const by_state = {};
    INTENT_STATES.forEach((s) => { by_state[s] = 0; });
    intents.forEach((i) => { by_state[i.state] = (by_state[i.state] || 0) + 1; });
    return {
      total: intents.length,
      by_state: by_state,
      terminal: intents.filter((i) => i.state === "COMPLETED" || i.state === "FAILED" || i.state === "CANCELLED").length,
      active: intents.filter((i) => i.state === "ACTIVE" || i.state === "WAITING_AUTHORIZATION").length,
      blocked: intents.filter((i) => i.state === "BLOCK" || i.state === "ESCALATE" || i.state === "HOLD").length,
    };
  }

  // ---- EXPORT ----
  global.OSX_INTENT = {
    STATES: INTENT_STATES,
    CLASSES: INTENT_CLASSES,
    TRANSITIONS: INTENT_TRANSITIONS,
    RISK_LEVELS: RISK_LEVELS,
    newIntent: newIntent,
    transition: transition,
    decompose: decompose,
    summary: summary,
    SAMPLE: SAMPLE_INTENTS,
  };
})(typeof window !== "undefined" ? window : global);
