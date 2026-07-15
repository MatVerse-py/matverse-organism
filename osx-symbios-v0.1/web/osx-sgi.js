/* =================================================================
   osx-sgi.js  ·  Relatório SGI Export (Page 5 of 5)
   =================================================================
   Governed export of SGI (SymbiOS Governance Indicators). Each
   metric must carry its own provenance — name, formula, formula
   version, source, period, method, evidence, uncertainty,
   responsible.

   5 epistemic states (the rule of export):
     OBSERVED          → can be published as observation
     COMPUTED          → can be published with formula + input
     REPORTED          → must be labelled as 3rd-party declaration
     PROPOSED          → cannot appear as result
     ESTIMATED         → cannot appear as consolidated indicator
     NOT_VALIDATED     → cannot appear as consolidated indicator

   Export formats:
     JSON, CSV, Markdown, PDF (manifest only), Evidence Pack,
     OpenLineage event, in-toto attestation
   ================================================================= */
(function (global) {
  "use strict";

  // ---- 6 epistemic states of a metric ----
  const METRIC_EPISTEMIC = [
    "OBSERVED", "COMPUTED", "REPORTED", "PROPOSED", "ESTIMATED", "NOT_VALIDATED",
  ];

  // ---- the 4 cardinal rules of export ----
  const EXPORT_RULES = {
    OBSERVED:       { can_publish: true,  must_label: false, requires_attestation: false },
    COMPUTED:       { can_publish: true,  must_label: false, requires_attestation: false },
    REPORTED:       { can_publish: true,  must_label: true,  requires_attestation: false },
    PROPOSED:       { can_publish: false, must_label: false, requires_attestation: false },
    ESTIMATED:      { can_publish: false, must_label: false, requires_attestation: false },
    NOT_VALIDATED:  { can_publish: false, must_label: false, requires_attestation: false },
  };

  // ---- 7 export formats ----
  const EXPORT_FORMATS = [
    "JSON", "CSV", "MARKDOWN", "PDF_MANIFEST",
    "EVIDENCE_PACK", "OPENLINEAGE_EVENT", "INTOTO_ATTESTATION",
  ];

  // ---- SGIMetric entity ----
  function newMetric(opts) {
    opts = opts || {};
    return {
      metric_id: opts.metric_id || ("M-" + Date.now().toString(16) + "-" + Math.floor(Math.random() * 0xffff).toString(16)),
      name: opts.name || "",
      formula: opts.formula || "",
      formula_version: opts.formula_version || "v1",
      source: opts.source || "",
      period: opts.period || "",
      method: opts.method || "",
      epistemic: opts.epistemic || "NOT_VALIDATED",
      evidence: opts.evidence || [],
      uncertainty: opts.uncertainty || null,
      responsible: opts.responsible || "",
      value: opts.value !== undefined ? opts.value : null,
      unit: opts.unit || "",
    };
  }

  // ---- gate: can a metric appear in the consolidated report? ----
  function canPublish(metric) {
    return EXPORT_RULES[metric.epistemic] ? EXPORT_RULES[metric.epistemic].can_publish : false;
  }
  function mustLabel(metric) {
    return EXPORT_RULES[metric.epistemic] ? EXPORT_RULES[metric.epistemic].must_label : false;
  }
  function requiresAttestation(metric) {
    return EXPORT_RULES[metric.epistemic] ? EXPORT_RULES[metric.epistemic].requires_attestation : false;
  }

  // ---- Seeded SGI metrics (deterministic, governed) ----
  const SAMPLE_METRICS = [
    newMetric({
      metric_id: "M-OMEGA-001",
      name: "Omega-Score (Ω) · constitutional viability",
      formula: "omega_score(c_inv, pbr/30, r_rec/5, a_aut, f_ant) = (D1·D2·D3·D4·D5)^(1/5)",
      formula_version: "v3.6.0",
      source: "matverse/omega.py + tests/test_omega.py",
      period: "2026-07-15 (per release)",
      method: "5-dim geometric mean, all dims in [0,1]",
      epistemic: "COMPUTED",
      evidence: ["tests/test_omega.py::test_canonical_closure_v36"],
      uncertainty: 0.05,
      responsible: "Mateus + MatVerse Organism v3.8.0",
      value: 0.81,
      unit: "score (0..1)",
    }),
    newMetric({
      metric_id: "M-TEST-001",
      name: "Test pass rate",
      formula: "pass_count / total_count",
      formula_version: "v1",
      source: "python3 -m unittest discover -s tests",
      period: "2026-07-15",
      method: "unittest discover + OK output",
      epistemic: "OBSERVED",
      evidence: ["CI log: 289/289 OK"],
      uncertainty: 0.0,
      responsible: "MatVerse CI",
      value: 1.0,
      unit: "ratio (0..1)",
    }),
    newMetric({
      metric_id: "M-MNB-001",
      name: "MMNB cross-run lineage length",
      formula: "count of MMNB generations linked via parent_id",
      formula_version: "v3.7.0",
      source: "validation/mmnb/lineage.json",
      period: "2026-07-15",
      method: "JSON tree traversal + parent link check",
      epistemic: "OBSERVED",
      evidence: ["validation/mmnb/lineage.json", "tests/test_mmnb.py"],
      uncertainty: 0.0,
      responsible: "Mateus + MatVerse Organism",
      value: 4,
      unit: "generations",
    }),
    newMetric({
      metric_id: "M-RR-001",
      name: "Receipt replay rate",
      formula: "replayed / total",
      formula_version: "v1",
      source: "validation/receipts/ + EvidenceOS log",
      period: "2026-07-15",
      method: "replay count vs total receipt count",
      epistemic: "REPORTED",
      evidence: ["OSX v0.1 EvidenceOS page"],
      uncertainty: 0.10,
      responsible: "EvidenceOS (reported by operator)",
      value: 0.67,
      unit: "ratio (0..1)",
    }),
    newMetric({
      metric_id: "M-AGENT-001",
      name: "Active agents in registry",
      formula: "count(agents where status=ACTIVE)",
      formula_version: "v1",
      source: "OSX Catálogo de Perfis",
      period: "2026-07-15",
      method: "registry scan",
      epistemic: "OBSERVED",
      evidence: ["osx-symbios-v0.1/web/osx-profiles.js::AGENTS"],
      uncertainty: 0.0,
      responsible: "OSX v0.1",
      value: 9,
      unit: "agents",
    }),
    newMetric({
      metric_id: "M-PROPOSED-001",
      name: "URANO survival uplift (PROPOSED, not yet validated)",
      formula: "unknown — needs P3 shadow evaluator",
      formula_version: "n/a",
      source: "NB-URANO-001",
      period: "n/a",
      method: "n/a",
      epistemic: "PROPOSED",
      evidence: [],
      uncertainty: null,
      responsible: "n/a",
      value: null,
      unit: "ratio (0..1)",
    }),
    newMetric({
      metric_id: "M-ESTIMATED-001",
      name: "OSS adoption uplift (ESTIMATED, not validated)",
      formula: "self-reported",
      formula_version: "n/a",
      source: "n/a",
      period: "n/a",
      method: "estimate",
      epistemic: "ESTIMATED",
      evidence: [],
      uncertainty: 0.50,
      responsible: "n/a",
      value: 0.30,
      unit: "ratio (0..1)",
    }),
    newMetric({
      metric_id: "M-NV-001",
      name: "Sepolia anchor uptime (NOT_VALIDATED, requires Ethereum tooling)",
      formula: "n/a",
      formula_version: "n/a",
      source: "n/a",
      period: "n/a",
      method: "n/a",
      epistemic: "NOT_VALIDATED",
      evidence: [],
      uncertainty: null,
      responsible: "n/a",
      value: null,
      unit: "%",
    }),
  ];

  // ---- filter metrics that can be published ----
  function publishable(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    return metrics.filter(canPublish);
  }
  function blocked(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    return metrics.filter((m) => !canPublish(m));
  }

  // ---- export to JSON ----
  function toJSON(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    return JSON.stringify({
      report_id: "SGI-" + Date.now().toString(16),
      generated_at: 0,
      metric_count: metrics.length,
      publishable_count: publishable(metrics).length,
      blocked_count: blocked(metrics).length,
      metrics: metrics.map((m) => Object.assign({}, m, {
        _governance: {
          can_publish: canPublish(m),
          must_label: mustLabel(m),
          requires_attestation: requiresAttestation(m),
        },
      })),
    }, null, 2);
  }

  // ---- export to CSV (one row per metric) ----
  function toCSV(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    const cols = ["metric_id", "name", "epistemic", "value", "unit", "uncertainty", "formula_version", "responsible", "can_publish", "must_label"];
    const rows = [cols.join(",")];
    metrics.forEach((m) => {
      rows.push(cols.map((c) => {
        if (c === "can_publish" || c === "must_label") {
          return m._governance ? (m._governance[c] ? "true" : "false") : (canPublish(m) ? "true" : "false");
        }
        const v = (c === "can_publish" || c === "must_label") ? (m._governance ? m._governance[c] : canPublish(m)) : m[c];
        const s = v === null || v === undefined ? "" : String(v);
        return s.includes(",") || s.includes('"') ? ('"' + s.replace(/"/g, '""') + '"') : s;
      }).join(","));
    });
    return rows.join("\n");
  }

  // ---- export to Markdown ----
  function toMarkdown(metrics) {
    metrics = metrics || publishable(metrics || SAMPLE_METRICS);
    const lines = [];
    lines.push("# SGI Report");
    lines.push("");
    lines.push("Generated by OSX v0.1 — governed export with provenance per metric.");
    lines.push("");
    lines.push("| metric_id | name | epistemic | value | unit | formula_version | can_publish | must_label |");
    lines.push("|-----------|------|-----------|-------|------|-----------------|-------------|------------|");
    metrics.forEach((m) => {
      lines.push("| " + [m.metric_id, m.name, m.epistemic, m.value === null ? "n/a" : m.value, m.unit, m.formula_version, canPublish(m) ? "YES" : "NO", mustLabel(m) ? "YES" : "NO"].join(" | ") + " |");
    });
    return lines.join("\n");
  }

  // ---- export to OpenLineage event (simplified) ----
  function toOpenLineageEvent(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    return JSON.stringify({
      eventType: "COMPLETE",
      eventTime: new Date().toISOString(),
      producer: "https://matverse.local/osx/v0.1",
      schemaURL: "https://openlineage.io/spec/2-0-2/OpenLineage.json#/definitions/RunEvent",
      run: { runId: "sgi-" + Date.now().toString(16) },
      job: { namespace: "matverse", name: "sgi-export" },
      inputs: metrics.filter(canPublish).map((m) => ({ namespace: "matverse", name: m.metric_id })),
      outputs: metrics.filter(canPublish).map((m) => ({ namespace: "matverse", name: m.metric_id, outputFacets: { _governance: { can_publish: true } } })),
      blocked: metrics.filter((m) => !canPublish(m)).map((m) => ({ metric_id: m.metric_id, epistemic: m.epistemic })),
    }, null, 2);
  }

  // ---- export to in-toto attestation (simplified SLSA) ----
  function toInTotoAttestation(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    return JSON.stringify({
      _type: "https://in-toto.io/Statement/v0.1",
      predicateType: "https://slsa.dev/provenance/v0.2",
      subject: metrics.filter(canPublish).map((m) => ({ name: m.metric_id, digest: { sha256: m.metric_id + "-hash" } })),
      predicate: {
        builder: { id: "https://matverse.local/osx/v0.1" },
        invocation: { configSource: { uri: "git+https://github.com/MatVerse-py/matverse-organism", digest: { sha256: "v3.8.0-release" } } },
        metadata: { buildStartedOn: new Date().toISOString() },
        materials: metrics.map((m) => ({ uri: m.source, digest: { sha256: m.metric_id + "-mat" } })),
      },
    }, null, 2);
  }

  // ---- gate: which metrics are blocked, with reason ----
  function gateReport(metrics) {
    metrics = metrics || SAMPLE_METRICS;
    const out = { publishable: [], blocked: [] };
    metrics.forEach((m) => {
      if (canPublish(m)) {
        out.publishable.push({ metric_id: m.metric_id, name: m.name, epistemic: m.epistemic, must_label: mustLabel(m) });
      } else {
        out.blocked.push({
          metric_id: m.metric_id,
          name: m.name,
          epistemic: m.epistemic,
          reason: {
            PROPOSED:      "PROPOSED metrics cannot appear as result (per SGI rule)",
            ESTIMATED:     "ESTIMATED metrics cannot appear as consolidated indicator",
            NOT_VALIDATED: "NOT_VALIDATED metrics cannot appear as consolidated indicator",
          }[m.epistemic] || "unknown epistemic state",
        });
      }
    });
    return out;
  }

  // ---- summary ----
  function summary() {
    const by_epistemic = {};
    METRIC_EPISTEMIC.forEach((s) => { by_epistemic[s] = 0; });
    SAMPLE_METRICS.forEach((m) => { by_epistemic[m.epistemic] = (by_epistemic[m.epistemic] || 0) + 1; });
    return {
      total: SAMPLE_METRICS.length,
      publishable: publishable().length,
      blocked: blocked().length,
      by_epistemic: by_epistemic,
      formats: EXPORT_FORMATS.length,
    };
  }

  // ---- EXPORT ----
  global.OSX_SGI = {
    EPISTEMIC_STATES: METRIC_EPISTEMIC,
    EXPORT_RULES: EXPORT_RULES,
    EXPORT_FORMATS: EXPORT_FORMATS,
    SAMPLE_METRICS: SAMPLE_METRICS,
    canPublish: canPublish,
    mustLabel: mustLabel,
    requiresAttestation: requiresAttestation,
    publishable: publishable,
    blocked: blocked,
    gateReport: gateReport,
    toJSON: toJSON,
    toCSV: toCSV,
    toMarkdown: toMarkdown,
    toOpenLineageEvent: toOpenLineageEvent,
    toInTotoAttestation: toInTotoAttestation,
    summary: summary,
    newMetric: newMetric,
  };
})(typeof window !== "undefined" ? window : global);
