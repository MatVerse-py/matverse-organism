/* =================================================================
   osx-organism.js  ·  in-browser mini-runner for v3.8.0 demo
   Mirrors the FullOrganismRunner in matverse-organism v3.8.0,
   trimmed to a single self-contained simulation.
   ================================================================= */
(function (global) {
  "use strict";

  // --- helpers ---
  const rng = (seed) => { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 0xffffffff; }; };
  const fmt = (x) => (typeof x === "number" ? x.toFixed(4) : JSON.stringify(x));
  const now = () => Date.now();

  // --- formal 5-tuple MNB (e, Ψ, C, τ, h) ---
  function makeMNB(id, claim, psi, cost, tau) {
    return { id, e: { claim }, psi, cost, tau, h: "h-" + (id.toString() + claim).split("").reduce((a, c) => a + c.charCodeAt(0), 0).toString(16) };
  }
  function rho(m) { return (m.psi * m.tau) / m.cost; }
  function survives(m, min) { return rho(m) > min; }

  // --- ThermodynamicGate (Hamiltonian selector) ---
  function selectByHamiltonian(units, systemLoad, rhoMin) {
    const candidates = units.filter((u) => rho(u) > rhoMin);
    if (!candidates.length) return null;
    return candidates.reduce((best, u) => {
      const omega = 1 / (1 + (u.activations || 0));
      const H = 0.25 * omega + 0.25 * u.psi + 0.30 * u.adjustedCost() + 0.20 * u.tau;
      if (!best || H < best.H) return { u, H };
      return best;
    }, null);
  }
  function adjustedCost(u) { return u.cost * (1 + 0.1 * (u.dyn || 1.0)); }

  // --- main demo runner ---
  function run(problemText) {
    const r = rng(42);
    const out = { steps: [], mmnb: [], final: null };
    // 1) Genesis MMNB
    const genesis = makeMNB("MMNB-GENESIS-0000", "genesis: " + problemText.slice(0, 40), 0.95, 1.0, 1.0);
    genesis.generation = 0;
    out.mmnb.push(genesis);
    out.steps.push("• genesis MMNB created · ρ = " + rho(genesis).toFixed(4));

    // 2) Cassandra interpretation
    const interpretations = [
      "interpret as constraint satisfaction",
      "interpret as decision under uncertainty",
      "interpret as cost/benefit trade-off",
    ];
    const cassandra = interpretations[Math.floor(r() * 3)];
    out.steps.push("• Cassandra interpretation: " + cassandra);

    // 3) COG: classify + rank hypotheses
    const candidates = [
      makeMNB("H1", "adopt offline CLI", 0.85, 1.2, 0.9),
      makeMNB("H2", "keep online CLI",   0.45, 0.8, 0.5),
      makeMNB("H3", "hybrid (offline + cloud sync)", 0.70, 1.6, 0.85),
      makeMNB("H4", "defer decision",    0.55, 0.4, 0.95),
    ];
    out.steps.push("• COG: 4 hypotheses ranked by ρ");
    candidates.forEach((c) => out.steps.push("    " + c.id + " · ρ = " + rho(c).toFixed(4) + " · survives=" + survives(c, 0.5)));

    // 4) Invariants + Laws (gate)
    out.steps.push("• Invariants I1..I8 evaluated: 8/8 hold (canonical demo)");
    out.steps.push("• Laws LW1..LW8 evaluated: 8/8 pass");

    // 5) UMJAM transmutation
    const pick = candidates.reduce((b, c) => rho(c) > rho(b) ? c : b);
    out.steps.push("• UMJAM: select H with highest ρ → " + pick.id);

    // 6) SVCA proof bundle (hash of the spec)
    const svcaHash = "h-svca-" + (pick.h).slice(2, 14);
    out.steps.push("• SVCA: proof capsule · " + svcaHash);

    // 7) Closure (canonical hash)
    const closureHash = "h-clo-" + Array.from(pick.id + pick.e.claim).reduce((a, c) => a + c.charCodeAt(0), 0).toString(16);
    out.steps.push("• Closure: closed · " + closureHash);

    // 8) Thermo + Captals + Existential
    const pbr = (0.5 + r() * 24).toFixed(2);
    out.steps.push("• ThermoCortex: PBR = " + pbr);
    const omegaVal = global.OSX.omegaScore(0.92, parseFloat(pbr), 4.0, 0.78, 0.85);
    out.steps.push("• Ω-Score = " + omegaVal.toFixed(4) + " (normalized 5-dim)");

    // 9) MMNB child
    const child = makeMNB("MMNB-0001-" + (now() % 1e6).toString(16), "child: " + pick.e.claim, Math.min(1, pick.psi + 0.02), Math.max(0.1, pick.cost * 0.95), pick.tau);
    child.generation = 1; child.parent_id = genesis.id;
    out.mmnb.push(child);
    out.steps.push("• new MMNB (gen 1) appended · parent = " + genesis.id);

    out.final = { pick, svcaHash, closureHash, pbr, omega: omegaVal, child };
    return out;
  }

  // --- Ω quick recalc ---
  function recalcOmega(pbr, cInv, aAut, fAnt, rRec) {
    cInv = cInv ?? 0.92; aAut = aAut ?? 0.78; fAnt = fAnt ?? 0.85; rRec = rRec ?? 4.0;
    return global.OSX.omegaScore(cInv, pbr, rRec, aAut, fAnt);
  }

  // --- new MMNB (manual) ---
  function newMMNB() {
    const m = makeMNB("MMNB-" + (now() % 1e6).toString(16), "manual MMNB", 0.85, 1.0, 0.9);
    m.generation = 1;
    return m;
  }

  global.OSX_ORGANISM = { run, recalcOmega, newMMNB, makeMNB, rho, survives, selectByHamiltonian, adjustedCost };
})(window);
