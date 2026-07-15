/* osx-symbios smoke test (SymbiOS module · 5 new pages) */
const fs = require('fs');
const vm = require('vm');

function makeCtx() {
  const noop = () => {};
  const elements = {};
  const document = {
    readyState: 'complete',
    addEventListener: noop,
    getElementById: (id) => elements[id] || null,
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  return { window: { addEventListener: noop, dispatchEvent: noop, OSX: undefined }, document, elements, addEventListener: noop, dispatchEvent: noop };
}

function load(files) {
  const ctx = makeCtx();
  ctx.global = ctx;
  vm.createContext(ctx);
  const code = files.map((f) => fs.readFileSync(f, 'utf8')).join('\n');
  vm.runInContext(code, ctx);
  return ctx;
}

function get(ctx, name) { return ctx.window[name] || ctx[name]; }

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exit(1); }
  console.log('  PASS:', msg);
}

console.log('=== osx-symbios-v0.1 · SymbiOS module smoke (5 pages) ===\n');

const BASE = '../web/';

// ---- 1) INTENT (Page 1) ----
console.log('[1] osx-intent.js (Gerenciador de Intenções)');
let ctx = load([BASE + 'osx-intent.js']);
let I = get(ctx, 'OSX_INTENT');
assert(I, 'exports OSX_INTENT');
assert(I.STATES.length === 12, '12 intent states');
assert(I.CLASSES.length === 6, '6 intent classes');
assert(I.RISK_LEVELS.length === 4, '4 risk levels');
assert(I.SAMPLE.length === 6, '6 seeded intents');
assert(I.SAMPLE.filter((i) => i.state === "ESCALATE").length === 1, '1 ESCALATE seed (INT-0003 deploy)');
assert(I.SAMPLE.filter((i) => i.external_effect).length === 2, '2 intents with external_effect');
let intent = I.newIntent({ statement: "publique v3.8.0 no Zenodo", intent_class: "PUBLICATION_AND_PROOF", external_effect: true, risk: "HIGH" });
assert(intent.state === "RECEIVED", 'new intent starts at RECEIVED');
let t = I.transition(intent, "CLASSIFIED");
assert(t.ok, 'transition RECEIVED→CLASSIFIED ok');
let dec = I.decompose(intent);
assert(dec.routing === "WAITING_AUTHORIZATION", 'publication routing → WAITING_AUTHORIZATION');
let t2 = I.transition(intent, "DECOMPOSED");
assert(t2.ok, 'transition CLASSIFIED→DECOMPOSED ok');
let t3 = I.transition(intent, "ROUTED");
assert(t3.ok, 'transition DECOMPOSED→ROUTED ok');
let t4 = I.transition(intent, "WAITING_AUTHORIZATION");
assert(t4.ok, 'transition ROUTED→WAITING_AUTHORIZATION ok');
// illegal transition
let tBad = I.transition(intent, "COMPLETED");
assert(!tBad.ok && tBad.reason === "illegal_transition", 'illegal transition blocked');
// deploy with external_effect → ESCALATE
let dep = I.newIntent({ intent_class: "EXECUTION_AND_DEPLOY", external_effect: true, risk: "CRITICAL" });
let dDep = I.decompose(dep);
assert(dDep.routing === "ESCALATE", 'deploy+external → ESCALATE routing');
// summary
let sum = I.summary(I.SAMPLE);
assert(sum.total === 6, 'summary.total === 6');
assert(sum.blocked === 1, 'summary.blocked === 1 (ESCALATE)');

// ---- 2) PROFILES (Page 2) ----
console.log('\n[2] osx-profiles.js (Catálogo de Perfis)');
ctx = load([BASE + 'osx-profiles.js']);
let P = get(ctx, 'OSX_PROFILES');
assert(P, 'exports OSX_PROFILES');
assert(Object.keys(P.CATALOGS).length === 5, '5 agent catalogs (CASSANDRA / ATLAS / URANO / SYMBIOS / EVIDENCEOS)');
assert(P.AXIS_8.length === 8, '8 AXIS-8 review skills');
assert(P.ROLES.length === 5, '5 RBAC roles');
assert(P.PERMISSIONS.length >= 12, '>= 12 permissions');
assert(P.USERS.length === 2, '2 users (Mateus + Cassandra Human)');
assert(P.AGENTS.length >= 10, '>= 10 agents in registry');
let agent = P.findAgent("AGT-CASS-INTERPRETER");
assert(agent && agent.status === "ACTIVE", 'findAgent: AGT-CASS-INTERPRETER is ACTIVE');
let role = P.findRole("ROLE-OPERATOR");
assert(role && role.permissions.length >= 3, 'ROLE-OPERATOR has >= 3 permissions');
let cassAgents = P.agentsByCatalog("CASSANDRA");
assert(cassAgents.length === 2, '2 agents in CASSANDRA catalog');
let grants = P.grantsForAgent("AGT-CASS-INTERPRETER");
assert(grants.length === 1, '1 grant for Cassandra interpreter');
assert(P.isGrantValid(grants[0]), 'grant is valid at t=0');
// expired grant
let expired = { issued_at: 0, ttl_seconds: 60 };
assert(!P.isGrantValid(expired, 100), 'expired grant detected');
// RBAC + capability separation
assert(P.findPermission("AGENT.DEPLOY") !== null, 'AGENT.DEPLOY permission exists');
let summaryP = P.summary();
assert(summaryP.catalogs === 5, 'summary catalogs=5');
assert(summaryP.axis_8 === 8, 'summary axis_8=8');

// ---- 3) NODES (Page 3) ----
console.log('\n[3] osx-nodes.js (Mapa de Nós SymbiOS)');
ctx = load([BASE + 'osx-nodes.js']);
let N = get(ctx, 'OSX_NODES');
assert(N, 'exports OSX_NODES');
assert(N.NODE_TYPES.length === 15, '15 node types');
assert(N.RELATION_TYPES.length === 15, '15 relation types');
assert(Object.keys(N.LENS_OF).length === 15, '15 lens mappings');
let n = N.newNode({ type: "HUMAN", label: "test" });
assert(n.lens === "physical", 'HUMAN → physical lens');
let e = N.newEdge({ source_id: "A", target_id: "B", type: "CONTAINS" });
assert(e.weight === 1.0, 'default edge weight = 1.0');
assert(N.NODES.length >= 25, '>= 25 seeded nodes');
assert(N.EDGES.length >= 30, '>= 30 seeded edges');
let macro = N.MACRO();
assert(macro.length === 3, 'MACRO = 3 (Mateus + Cassandra Human + MatVerse)');
let meso = N.MESO();
assert(meso.length >= 5, 'MESO >= 5 (notebooks + agents + experiments)');
let micro = N.MICRO();
assert(micro.length >= 5, 'MICRO >= 5 (cells + executions + receipts)');
let inf = N.nodesByLens("informational");
assert(inf.length >= 5, 'informational lens has >= 5 nodes');
let dig = N.nodesByLens("digital");
assert(dig.length >= 5, 'digital lens has >= 5 nodes');
let phy = N.nodesByLens("physical");
assert(phy.length >= 2, 'physical lens has >= 2 nodes');
let nbrs = N.neighborsOf("NODE-MATEUS", 1);
assert(nbrs.length >= 1, 'Mateus has >= 1 neighbor');
let sumN = N.summary();
assert(sumN.total_nodes >= 25, 'summary total_nodes >= 25');
assert(sumN.total_edges >= 30, 'summary total_edges >= 30');
// SUPERSEDES + CONTRADICTS edges exist
let supersedes = N.EDGES.filter((e) => e.type === "SUPERSEDES");
assert(supersedes.length >= 1, '>= 1 SUPERSEDES edge');
let contradicts = N.EDGES.filter((e) => e.type === "CONTRADICTS");
assert(contradicts.length >= 1, '>= 1 CONTRADICTS edge');

// ---- 4) EVIDENCE (Page 4) ----
console.log('\n[4] osx-evidence.js (Protocolos EvidenceOS)');
ctx = load([BASE + 'osx-evidence.js']);
let E = get(ctx, 'OSX_EVIDENCE');
assert(E, 'exports OSX_EVIDENCE');
assert(E.STATES.length === 10, '10 evidence states');
assert(Object.keys(E.TRANSITIONS).length === 10, '10 transitions defined');
let proto = E.newProtocol({ protocol_id: "PROT-TEST", type: "TEST" });
assert(proto.protocol_id === "PROT-TEST", 'newProtocol sets id');
let dec2 = E.newDecision({ decision_id: "DEC-T", status: "PREPARED" });
assert(dec2.status === "PREPARED", 'newDecision starts at PREPARED');
let t1 = E.transition(dec2, "HOLD");
assert(t1.ok, 'PREPARED → HOLD ok');
let t1b = E.transition(dec2, "PASS_LOCAL");
assert(t1b.ok, 'HOLD → PASS_LOCAL ok');
let rcp = E.newReceipt({ receipt_id: "RCP-T" });
assert(rcp.replay_status === "NOT_REPLAYED", 'newReceipt: NOT_REPLAYED');
let led = E.newLedger();
let e1 = led.append(rcp);
assert(e1.hash !== "h-root-0", 'ledger appends entry with new hash');
let e2 = led.append(E.newReceipt({ receipt_id: "RCP-T2", hash_in: "h-2", hash_out: "h-out-2" }));
assert(led.verify(), 'ledger is valid after 2 appends');
let bad = E.newLedger();
bad.entries.push({ receipt_id: "BAD", hash: "h-1", prev_hash: "h-ROOT-WRONG" });
assert(!bad.verify(), 'tampered ledger is invalid');
// full chain verify
let chain = E.verifyChain(E.SAMPLE_DECISIONS[0], E.SAMPLE_RECEIPTS[0], E.SAMPLE_LEDGER, E.SAMPLE_REPLAYS);
assert(chain.verdict !== null, 'verifyChain returns verdict');
assert(typeof chain.ledger_valid === "boolean", 'verifyChain has ledger_valid field');
let sumE = E.summary();
assert(sumE.protocols === 3, '3 sample protocols');
assert(sumE.decisions === 3, '3 sample decisions');
assert(sumE.receipts === 3, '3 sample receipts');
assert(sumE.ledger_entries === 3, '3 ledger entries (one per receipt)');
assert(sumE.ledger_valid, 'sample ledger is valid');

// ---- 5) SGI (Page 5) ----
console.log('\n[5] osx-sgi.js (Relatório SGI Export)');
ctx = load([BASE + 'osx-sgi.js']);
let S = get(ctx, 'OSX_SGI');
assert(S, 'exports OSX_SGI');
assert(S.EPISTEMIC_STATES.length === 6, '6 epistemic states');
assert(S.EXPORT_FORMATS.length === 7, '7 export formats');
assert(S.SAMPLE_METRICS.length >= 7, '>= 7 sample metrics');
let observed = S.SAMPLE_METRICS.filter((m) => m.epistemic === "OBSERVED");
assert(observed.every((m) => S.canPublish(m)), 'all OBSERVED metrics can publish');
let proposed = S.SAMPLE_METRICS.filter((m) => m.epistemic === "PROPOSED");
assert(proposed.every((m) => !S.canPublish(m)), 'all PROPOSED metrics are blocked');
let estimated = S.SAMPLE_METRICS.filter((m) => m.epistemic === "ESTIMATED");
assert(estimated.every((m) => !S.canPublish(m)), 'all ESTIMATED metrics are blocked');
let nv = S.SAMPLE_METRICS.filter((m) => m.epistemic === "NOT_VALIDATED");
assert(nv.every((m) => !S.canPublish(m)), 'all NOT_VALIDATED metrics are blocked');
let reported = S.SAMPLE_METRICS.filter((m) => m.epistemic === "REPORTED");
assert(reported.every((m) => S.mustLabel(m)), 'all REPORTED metrics must_label=true');
let pub = S.publishable();
let blk = S.blocked();
assert(pub.length + blk.length === S.SAMPLE_METRICS.length, 'publishable + blocked = total');
let json = S.toJSON();
assert(json.includes("publishable_count"), 'JSON export has publishable_count');
assert(json.includes("must_label"), 'JSON export has must_label');
let csv = S.toCSV();
assert(csv.split("\n").length === S.SAMPLE_METRICS.length + 1, 'CSV has header + one row per metric');
let md = S.toMarkdown(pub);
assert(md.includes("# SGI Report"), 'Markdown export has title');
let ol = S.toOpenLineageEvent();
assert(ol.includes("eventType"), 'OpenLineage event has eventType');
let it = S.toInTotoAttestation();
assert(it.includes("in-toto.io/Statement"), 'in-toto attestation has correct _type');
let gate = S.gateReport();
assert(gate.publishable.length === pub.length, 'gateReport.publishable matches');
assert(gate.blocked.every((b) => b.reason), 'all blocked metrics have reason');
let sumS = S.summary();
assert(sumS.publishable + sumS.blocked === sumS.total, 'summary publishable + blocked = total');

// ---- 6) Combined ----
console.log('\n[6] combined load (all 5 modules together)');
ctx = load([
  BASE + 'osx-core.js',
  BASE + 'osx-figure-lab.js',
  BASE + 'osx-canvas.js',
  BASE + 'osx-organism.js',
  BASE + 'osx-intent.js',
  BASE + 'osx-profiles.js',
  BASE + 'osx-nodes.js',
  BASE + 'osx-evidence.js',
  BASE + 'osx-sgi.js',
]);
assert(get(ctx, 'OSX'),            'OSX loaded');
assert(get(ctx, 'OSX_FIGURE_LAB'), 'OSX_FIGURE_LAB loaded');
assert(get(ctx, 'OSX_CANVAS'),     'OSX_CANVAS loaded');
assert(get(ctx, 'OSX_ORGANISM'),   'OSX_ORGANISM loaded');
assert(get(ctx, 'OSX_INTENT'),     'OSX_INTENT loaded');
assert(get(ctx, 'OSX_PROFILES'),   'OSX_PROFILES loaded');
assert(get(ctx, 'OSX_NODES'),      'OSX_NODES loaded');
assert(get(ctx, 'OSX_EVIDENCE'),   'OSX_EVIDENCE loaded');
assert(get(ctx, 'OSX_SGI'),        'OSX_SGI loaded');

console.log('\n=== ALL SYMBIOS SMOKE TESTS PASS ===');
