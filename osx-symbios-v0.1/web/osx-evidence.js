/* =================================================================
   osx-evidence.js  ·  Protocolos EvidenceOS (Page 4 of 5)
   =================================================================
   Proof + continuity layer. Tracks the FULL cycle:

     Intent → Policy → Ω-Gate → Decision → Execution →
     Observation → Receipt → Ledger → Replay

   10 states (constitutional, fail-closed):
     PREPARED, HOLD, PASS_LOCAL, BLOCK, ESCALATE,
     EXECUTED, OBSERVED, REPLAYED, WITNESSED_EXTERNAL, REVOKED

   Cardinal rules (per the corpus):
     Receipt  ≠ truth
     Ledger   ≠ scientific validation
     Replay   ≠ external witness
   ================================================================= */
(function (global) {
  "use strict";

  // ---- 10 evidence states ----
  const EVIDENCE_STATES = [
    "PREPARED", "HOLD", "PASS_LOCAL", "BLOCK", "ESCALATE",
    "EXECUTED", "OBSERVED", "REPLAYED", "WITNESSED_EXTERNAL", "REVOKED",
  ];

  // ---- valid transitions ----
  const EVIDENCE_TRANSITIONS = {
    PREPARED:           ["HOLD", "PASS_LOCAL", "BLOCK", "ESCALATE"],
    HOLD:               ["PREPARED", "PASS_LOCAL", "BLOCK", "ESCALATE", "REVOKED"],
    PASS_LOCAL:         ["EXECUTED", "BLOCK", "ESCALATE", "REVOKED"],
    BLOCK:              ["REVOKED", "PREPARED"],
    ESCALATE:           ["PASS_LOCAL", "BLOCK", "REVOKED", "HOLD"],
    EXECUTED:           ["OBSERVED", "ESCALATE", "REVOKED"],
    OBSERVED:           ["REPLAYED", "ESCALATE", "REVOKED"],
    REPLAYED:           ["WITNESSED_EXTERNAL", "ESCALATE", "REVOKED"],
    WITNESSED_EXTERNAL: ["REVOKED"],
    REVOKED:            [],
  };

  // ---- Protocol entity ----
  function newProtocol(opts) {
    opts = opts || {};
    return {
      protocol_id: opts.protocol_id || ("PROT-" + Date.now().toString(16) + "-" + Math.floor(Math.random() * 0xffff).toString(16)),
      version: opts.version || "v1",
      type: opts.type || "DEFAULT",
      policy: opts.policy || {},
      created_at: opts.created_at || 0,
    };
  }

  // ---- Decision entity ----
  function newDecision(opts) {
    opts = opts || {};
    return {
      decision_id: opts.decision_id || ("DEC-" + Date.now().toString(16) + "-" + Math.floor(Math.random() * 0xffff).toString(16)),
      policy_id: opts.policy_id || null,
      gate_id: opts.gate_id || null,
      intent_id: opts.intent_id || null,
      user_id: opts.user_id || null,
      agent_id: opts.agent_id || null,
      capability_id: opts.capability_id || null,
      status: opts.status || "PREPARED",  // PREPARED|HOLD|PASS_LOCAL|BLOCK|ESCALATE
      hash_in: opts.hash_in || "h-0",
      hash_out: opts.hash_out || null,
      prev_receipt: opts.prev_receipt || null,
      created_at: opts.created_at || 0,
    };
  }

  // ---- Receipt entity ----
  function newReceipt(opts) {
    opts = opts || {};
    return {
      receipt_id: opts.receipt_id || ("RCP-" + Date.now().toString(16) + "-" + Math.floor(Math.random() * 0xffff).toString(16)),
      execution_id: opts.execution_id || null,
      decision_id: opts.decision_id || null,
      agent_id: opts.agent_id || null,
      capability_id: opts.capability_id || null,
      hash_in: opts.hash_in || "h-0",
      hash_out: opts.hash_out || "h-0",
      prev_receipt: opts.prev_receipt || null,
      status: opts.status || "PREPARED",
      replay_status: opts.replay_status || "NOT_REPLAYED",  // NOT_REPLAYED|REPLAYED|FAILED
      witness_status: opts.witness_status || "NOT_WITNESSED", // NOT_WITNESSED|WITNESSED|DENIED
      created_at: opts.created_at || 0,
    };
  }

  // ---- Ledger entity (append-only hash chain) ----
  function newLedger() {
    let entries = [];
    let root_hash = "h-root-0";
    return {
      ledger_id: "LED-" + Date.now().toString(16),
      entries: entries,
      root_hash: root_hash,
      // ---- append a receipt (preserves hash chain) ----
      append: function (receipt) {
        const prev = entries[entries.length - 1];
        const prev_hash = prev ? prev.hash : "h-root-0";
        // pseudo hash chain: not crypto, just structural
        const new_entry = {
          receipt_id: receipt.receipt_id,
          hash_in: receipt.hash_in,
          hash_out: receipt.hash_out,
          prev_hash: prev_hash,
          hash: "h-" + (entries.length + 1).toString(16).padStart(4, "0") + "-chain",
        };
        entries.push(new_entry);
        root_hash = new_entry.hash;
        return new_entry;
      },
      verify: function () {
        // Walk the chain
        for (let i = 0; i < entries.length; i++) {
          if (i === 0) {
            if (entries[i].prev_hash !== "h-root-0") return false;
          } else {
            if (entries[i].prev_hash !== entries[i - 1].hash) return false;
          }
        }
        return true;
      },
    };
  }

  // ---- Replay entity ----
  function newReplay(opts) {
    opts = opts || {};
    return {
      replay_id: opts.replay_id || ("RPL-" + Date.now().toString(16) + "-" + Math.floor(Math.random() * 0xffff).toString(16)),
      receipt_id: opts.receipt_id || null,
      by_agent_id: opts.by_agent_id || null,
      status: opts.status || "QUEUED",  // QUEUED|RUNNING|REPLAYED|FAILED
      result_hash: opts.result_hash || null,
      compared_with_original: opts.compared_with_original || null,  // MATCH|MISMATCH|NOT_RUN
      witness_status: opts.witness_status || "NOT_WITNESSED",
      created_at: opts.created_at || 0,
    };
  }

  // ---- Sample chain (deterministic seed) ----
  const SAMPLE_PROTOCOLS = [
    newProtocol({ protocol_id: "PROT-RESEARCH-V1", version: "v1.0", type: "RESEARCH", policy: { risk: "MEDIUM" } }),
    newProtocol({ protocol_id: "PROT-PUBLISH-V1",  version: "v1.0", type: "PUBLISH",  policy: { risk: "HIGH", requires_operator: true } }),
    newProtocol({ protocol_id: "PROT-DEPLOY-V1",   version: "v1.0", type: "DEPLOY",   policy: { risk: "CRITICAL", requires_2_of_3: true } }),
  ];

  const SAMPLE_DECISIONS = [
    newDecision({ decision_id: "DEC-001", policy_id: "PROT-RESEARCH-V1", intent_id: "INT-0001", user_id: "USR-MATEUS", agent_id: "AGT-CASS-INTERPRETER", capability_id: "INTENT.INTERPRET", status: "PASS_LOCAL", hash_in: "h-in-001", hash_out: "h-out-001", created_at: 100 }),
    newDecision({ decision_id: "DEC-002", policy_id: "PROT-PUBLISH-V1",  intent_id: "INT-0002", user_id: "USR-MATEUS", agent_id: "AGT-EVD-LEDGER",        capability_id: "LEDGER.READ",      status: "PASS_LOCAL", hash_in: "h-in-002", hash_out: "h-out-002", created_at: 200 }),
    newDecision({ decision_id: "DEC-003", policy_id: "PROT-DEPLOY-V1",   intent_id: "INT-0003", user_id: "USR-MATEUS", agent_id: "AGT-SYM-DEPLOY",         capability_id: "NOTEBOOK.DEPLOY",  status: "ESCALATE",   hash_in: "h-in-003", hash_out: "h-out-003", created_at: 300 }),
  ];

  const SAMPLE_RECEIPTS = [
    newReceipt({ receipt_id: "RCP-001", execution_id: "EXE-001", decision_id: "DEC-001", agent_id: "AGT-CASS-INTERPRETER", capability_id: "INTENT.INTERPRET", hash_in: "h-in-001", hash_out: "h-out-001", status: "OBSERVED",  replay_status: "REPLAYED", witness_status: "NOT_WITNESSED", created_at: 110 }),
    newReceipt({ receipt_id: "RCP-002", execution_id: "EXE-002", decision_id: "DEC-002", agent_id: "AGT-EVD-LEDGER",       capability_id: "LEDGER.READ",      hash_in: "h-in-002", hash_out: "h-out-002", status: "OBSERVED",  replay_status: "REPLAYED", witness_status: "WITNESSED",     created_at: 210, prev_receipt: "RCP-001" }),
    newReceipt({ receipt_id: "RCP-003", execution_id: "EXE-003", decision_id: "DEC-003", agent_id: "AGT-SYM-DEPLOY",        capability_id: "NOTEBOOK.DEPLOY",  hash_in: "h-in-003", hash_out: null,         status: "ESCALATE", replay_status: "NOT_REPLAYED", witness_status: "NOT_WITNESSED", created_at: 310, prev_receipt: "RCP-002" }),
  ];

  // ---- Sample ledger (3-entry chain) ----
  const SAMPLE_LEDGER = newLedger();
  SAMPLE_RECEIPTS.forEach((r) => SAMPLE_LEDGER.append(r));

  // ---- Sample replays ----
  const SAMPLE_REPLAYS = [
    newReplay({ replay_id: "RPL-001", receipt_id: "RCP-001", by_agent_id: "AGT-EVD-REPLAY", status: "REPLAYED", result_hash: "h-out-001", compared_with_original: "MATCH",  witness_status: "NOT_WITNESSED", created_at: 150 }),
    newReplay({ replay_id: "RPL-002", receipt_id: "RCP-002", by_agent_id: "AGT-EVD-REPLAY", status: "REPLAYED", result_hash: "h-out-002", compared_with_original: "MATCH",  witness_status: "WITNESSED",     created_at: 250 }),
  ];

  // ---- State machine: transition ----
  function transition(record, next_state) {
    const allowed = EVIDENCE_TRANSITIONS[record.status] || [];
    if (allowed.indexOf(next_state) === -1) {
      return { ok: false, reason: "illegal_transition", from: record.status, to: next_state, allowed: allowed };
    }
    record.status = next_state;
    return { ok: true, record: record };
  }

  // ---- verify a full chain (decision → receipt → ledger → replay) ----
  function verifyChain(decision, receipt, ledger, replays) {
    replays = replays || [];
    const out = {
      decision_status: decision ? decision.status : null,
      receipt_status: receipt ? receipt.status : null,
      ledger_valid: ledger ? ledger.verify() : null,
      receipt_replayed: replays.some((r) => r.receipt_id === (receipt && receipt.receipt_id) && r.compared_with_original === "MATCH"),
      receipt_witnessed: !!(receipt && receipt.witness_status === "WITNESSED"),
      verdict: null,
    };
    // fail-closed: only WITNESSED_EXTERNAL counts as "witness"
    if (out.receipt_witnessed && out.ledger_valid && out.receipt_replayed) {
      out.verdict = "WITNESS_OK";
    } else if (out.receipt_status === "ESCALATE") {
      out.verdict = "ESCALATE_PENDING";
    } else if (!out.ledger_valid) {
      out.verdict = "LEDGER_BROKEN";
    } else {
      out.verdict = "OBSERVED_BUT_NOT_WITNESSED";
    }
    return out;
  }

  // ---- summary across the evidence chain ----
  function summary() {
    const by_state = {};
    EVIDENCE_STATES.forEach((s) => { by_state[s] = 0; });
    [...SAMPLE_DECISIONS, ...SAMPLE_RECEIPTS].forEach((r) => { by_state[r.status] = (by_state[r.status] || 0) + 1; });
    return {
      protocols: SAMPLE_PROTOCOLS.length,
      decisions: SAMPLE_DECISIONS.length,
      receipts: SAMPLE_RECEIPTS.length,
      ledger_entries: SAMPLE_LEDGER.entries.length,
      ledger_valid: SAMPLE_LEDGER.verify(),
      replays: SAMPLE_REPLAYS.length,
      by_state: by_state,
    };
  }

  // ---- EXPORT ----
  global.OSX_EVIDENCE = {
    STATES: EVIDENCE_STATES,
    TRANSITIONS: EVIDENCE_TRANSITIONS,
    newProtocol: newProtocol,
    newDecision: newDecision,
    newReceipt: newReceipt,
    newLedger: newLedger,
    newReplay: newReplay,
    transition: transition,
    verifyChain: verifyChain,
    summary: summary,
    SAMPLE_PROTOCOLS: SAMPLE_PROTOCOLS,
    SAMPLE_DECISIONS: SAMPLE_DECISIONS,
    SAMPLE_RECEIPTS: SAMPLE_RECEIPTS,
    SAMPLE_LEDGER: SAMPLE_LEDGER,
    SAMPLE_REPLAYS: SAMPLE_REPLAYS,
  };
})(typeof window !== "undefined" ? window : global);
