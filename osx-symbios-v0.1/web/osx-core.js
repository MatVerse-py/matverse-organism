/* =================================================================
   osx-core.js  ·  state, views, constitutional data
   Pure stdlib, no dependencies. Mirrors matverse-organism v3.8.0.
   ================================================================= */
(function (global) {
  "use strict";

  // ----------------- CONSTITUTIONAL DATA (v3.8.0) -----------------
  const ORGANS = [
    { id: "MMNB",                role: "causal memory (seed of the next cycle)" },
    { id: "CASSANDRA_METACORTEX", role: "cognitive interpretation + L3 learning" },
    { id: "COG",                role: "Hypothesis Field (Campo de Hipóteses)" },
    { id: "INVARIANTS",         role: "fail-closed constitutional gate (I1..I8)" },
    { id: "LAWS",               role: "versioned operational policies (LW1..LW8)" },
    { id: "UMJAM",              role: "admissible mutation" },
    { id: "SVCA",               role: "Application Video-Capsule (proof bundle)" },
    { id: "CLOSURE",            role: "closure compiler (4-projections + 2 macro)" },
    { id: "ATLAS",              role: "live cartographic projection" },
    { id: "THERMO_CORTEX",      role: "energy / PBR / regenerative accounting" },
    { id: "CAPTALS",            role: "continuity allocator + M-bit" },
    { id: "EXISTENTIAL",        role: "metabolism, autopoiesis, apoptosis, antifragility, homeostasis" },
  ];

  const PHYSICS = [
    { id: "GTHDL_HAMILTONIAN",   eq: "dρ/dt = -i[Ĥ_Σ, ρ]" },
    { id: "RIEMANNIAN_MANIFOLD", eq: "M = (O, R, g, Φ, ρ)" },
    { id: "EPISTEMIC_STATE",      eq: "8 states + Dempster-Shafer + Dung" },
  ];

  const INVARIANTS = [
    "I1  causal_identity                No execution without causal identity (MMNB ancestry).",
    "I2  prohibited_action_blocked      No prohibited action is ever authorized.",
    "I3  proof_over_narrative           No proof is replaced by a narrative.",
    "I4  evidence_before_fact           No hypothesis becomes fact without evidence.",
    "I5  lineage_preserved              No transformation erases its lineage.",
    "I6  epistemic_economic_separation  No economic token buys epistemic validity.",
    "I7  continuity_floor               No operation may consume resources required for continuity.",
    "I8  planetary_boundary             No regenerative claim without independent measurement.",
  ];

  // ----------------- NOTEBOOKS (initial state) -----------------
  const NOTEBOOKS = [
    {
      id: "NB-LIVING-PAPER",
      title: "Living Paper",
      epistemic: "EVD",
      cells: [
        { id: "CELL-001", type: "HYPOTHESIS", epistemic: "HYP", claim: "A 5-tuple MNB m = (e, Ψ, C, τ, h) is the canonical causal cell." },
        { id: "CELL-002", type: "CLAIM",      epistemic: "EVD", claim: "Value density ρ = Ψ·τ/C selects for memory survival." },
        { id: "CELL-003", type: "CLAIM",      epistemic: "ADM", claim: "GTHDL Hamiltonian governs organism evolution: dρ/dt = -i[Ĥ_Σ, ρ]." },
        { id: "CELL-004", type: "DECISION",   epistemic: "CON", claim: "v3.8.0 integrates the 5-tuple, the Hamiltonian, and the Riemannian manifold." },
        { id: "CELL-005", type: "PAPER",      epistemic: "CON", claim: "MatVerse Organism v3.8.0 — 253/253 tests, +15,273 LOC." },
      ],
    },
    {
      id: "NB-CASSANDRA",
      title: "Cassandra Copilot",
      epistemic: "EVD",
      cells: [
        { id: "CELL-010", type: "HYPOTHESIS", epistemic: "HYP", claim: "Cassandra interprets user intent as transformations of MNBs." },
        { id: "CELL-011", type: "EXPERIMENT", epistemic: "EVD", claim: "Local rule-based Cassandra routes commands to UMJAM/URANO/SymbiOS." },
        { id: "CELL-012", type: "RESULT",     epistemic: "ADM", claim: "Demo: 'crie hipótese sobre o experimento 4' → cell created with state HYP." },
      ],
    },
    {
      id: "NB-URANO-001",
      title: "URANO Laboratory",
      epistemic: "HYP",
      cells: [
        { id: "CELL-020", type: "HYPOTHESIS", epistemic: "HYP", claim: "Hamiltonian-selected MNBs minimize system cost under load." },
        { id: "CELL-021", type: "EXPERIMENT", epistemic: "HYP", claim: "Apply ThermodynamicGate to 1000 synthetic units, measure survival." },
        { id: "CELL-022", type: "EVIDENCE",   epistemic: "OBS", claim: "Survival correlates with value density (Spearman 0.91 in v0.1)." },
        { id: "CELL-023", type: "DECISION",   epistemic: "HYP", claim: "Hold for evidence pack; insufficient sample size to confirm." },
        { id: "CELL-024", type: "CLAIM",      epistemic: "INF", claim: "Manifold curvature may explain 'expensive knowledge' regions." },
      ],
    },
    {
      id: "NB-SYMBIOS",
      title: "SymbiOS Network",
      epistemic: "EVD",
      cells: [
        { id: "CELL-030", type: "HYPOTHESIS", epistemic: "HYP", claim: "SymbiOS is a Network Notebook, not a desktop." },
        { id: "CELL-031", type: "CLAIM",      epistemic: "EVD", claim: "Same object, three lenses: informational / digital / physical." },
        { id: "CELL-032", type: "EXPERIMENT", epistemic: "EVD", claim: "OSX v0.1 ships this 3-lens view." },
        { id: "CELL-033", type: "DECISION",   epistemic: "CON", claim: "Constitutional physics (GTHDL / Riemannian / Epistemic) govern the cycle." },
      ],
    },
    {
      id: "NB-ATLAS",
      title: "Atlas Registry",
      epistemic: "EVD",
      cells: [
        { id: "CELL-040", type: "CLAIM", epistemic: "EVD", claim: "Atlas holds the constitutional registry, source map, and claim graph." },
        { id: "CELL-041", type: "CLAIM", epistemic: "ADM", claim: "12 organs + 3 physics = 15 constitutional entries." },
        { id: "CELL-042", type: "DECISION", epistemic: "CON", claim: "OSX renders the registry table from this notebook." },
      ],
    },
    {
      id: "NB-EVIDENCE",
      title: "Evidence Pack",
      epistemic: "EVD",
      cells: [
        { id: "CELL-050", type: "EVIDENCE", epistemic: "EVD", claim: "v3.8.0: 253/253 unit tests pass (was 146/146 in v3.7.0)." },
        { id: "CELL-051", type: "EVIDENCE", epistemic: "EVD", claim: "MMNB chain: 4 generations across runs, no parent-lineage breaks." },
        { id: "CELL-052", type: "EVIDENCE", epistemic: "OBS", claim: "15 ACTIVE capabilities in the registry, 0 REVOKED, 0 BLOCKED." },
        { id: "CELL-053", type: "EVIDENCE", epistemic: "EVD", claim: "M-bit uses the canonical 6-dim formula (Q·R·T·V·E·H)^(1/6)·(1-risk)." },
        { id: "CELL-054", type: "EVIDENCE", epistemic: "EVD", claim: "Dung is conflict-free + self-defending (was only self-defending)." },
      ],
    },
  ];

  // ----------------- SEED: MMNB cross-run lineage -----------------
  const MMNB_LINEAGE = [
    { id: "MMNB-0000-...", generation: 0, decision: "—",          strategy: "GENESIS" },
    { id: "MMNB-0001-...", generation: 1, decision: "HOLD_ACTION", strategy: "H1" },
    { id: "MMNB-0002-...", generation: 2, decision: "HOLD_ACTION", strategy: "H1" },
    { id: "MMNB-0003-...", generation: 3, decision: "HOLD_ACTION", strategy: "H1" },
  ];

  // ----------------- CANONICAL 5-TUPLE MNB (illustrative) -----------------
  const SAMPLE_MNB = {
    e: { claim: "Riemannian manifold improves survival of rare skills by ~27%" },
    psi: 0.88,    // semantic coherence
    cost: 1.2,    // qualitative cost
    tau: 0.93,    // temporal persistence
    h: "h-7f3a2b1c9d4e5f6a8b0c1d2e3f4a5b6",  // cryptographic hash (illustrative)
  };
  SAMPLE_MNB.rho = (SAMPLE_MNB.psi * SAMPLE_MNB.tau) / SAMPLE_MNB.cost;

  // ----------------- VIEW SWITCHING -----------------
  function setView(name) {
    document.querySelectorAll(".osx-view").forEach((el) => el.classList.remove("is-active"));
    document.querySelectorAll(".osx-tab, .osx-dock-item").forEach((el) => el.classList.remove("is-active"));
    const view = document.querySelector(`.osx-view[data-view="${name}"]`);
    if (view) view.classList.add("is-active");
    document.querySelectorAll(`[data-view="${name}"]`).forEach((el) => el.classList.add("is-active"));
    global.dispatchEvent(new CustomEvent("osx:view", { detail: { name } }));
  }

  // ----------------- OMEGA SCORE (canonical 5-dim) -----------------
  function omegaScore(cInv, pbr, rRec, aAut, fAnt) {
    const D = [cInv, pbr / 30, rRec / 5, aAut, fAnt].map((x) => Math.max(0, Math.min(1, x)));
    if (D.some((d) => d <= 0)) return 0;
    return Math.pow(D.reduce((p, d) => p * d, 1), 1 / 5);
  }

  // ----------------- EPITEMIC STATE → GLYPH (for cognitive canvas) -----------------
  const EPISTEMIC_GLYPH = {
    OBS: "circle", INF: "diamond", HYP: "hexagon",
    EVD: "rect", ADM: "rect-bold", CON: "circle-bold",
    ESC: "diamond-blink", BLOCK: "block",
  };
  const EPISTEMIC_COLOR = {
    OBS: "#7a8290", INF: "#9b87f5", HYP: "#d6c25a",
    EVD: "#5fd2a4", ADM: "#5fd2a4", CON: "#5fd2a4",
    ESC: "#d97757", BLOCK: "#c44b4b",
  };

  // ----------------- REGISTRY DATA -----------------
  const REGISTRY = [
    { id: "MMNB",                type: "organ",    state: "ACTIVE",  desc: "First-class causal memory; on-disk JSON lineage." },
    { id: "RiemannianManifold",  type: "physics",  state: "ACTIVE",  desc: "M = (O, R, g, Φ, ρ); sparse 4-tensor in pure stdlib." },
    { id: "GTHDLPropagator",     type: "physics",  state: "ACTIVE",  desc: "dρ/dt = -i[Ĥ_Σ, ρ]; Taylor expansion for short dt." },
    { id: "EpistemicState",      type: "physics",  state: "ACTIVE",  desc: "NULL/OBS/INF/HYP/EVD/ADM/CON/ESCALATE." },
    { id: "ThermodynamicGate",   type: "organ",    state: "ACTIVE",  desc: "Hamiltonian-min selector; load-aware." },
    { id: "ApoptosisScheduler",  type: "organ",    state: "ACTIVE",  desc: "Retires capabilities over a failure-rate threshold." },
    { id: "OmegaScore",          type: "object",   state: "ACTIVE",  desc: "Ω = (D1·D2·D3·D4·D5)^(1/5); all dims in [0,1]." },
    { id: "FormalMNB",           type: "object",   state: "ACTIVE",  desc: "5-tuple (e, Ψ, C, τ, h); tamper detection via verify()." },
    { id: "CaptalsPublicToken",  type: "external", state: "HOLD",    desc: "Requires legal review per jurisdiction." },
    { id: "SepoliaAnchor",       type: "external", state: "HOLD",    desc: "Requires Ethereum tooling + operator signature." },
    { id: "IndependentReplay",   type: "external", state: "HOLD",    desc: "Requires second operator + second machine." },
  ];

  // ----------------- EXPORT -----------------
  global.OSX = {
    ORGANS, PHYSICS, INVARIANTS,
    NOTEBOOKS, MMNB_LINEAGE, SAMPLE_MNB,
    REGISTRY, EPISTEMIC_GLYPH, EPISTEMIC_COLOR,
    setView, omegaScore,
  };
})(window);
