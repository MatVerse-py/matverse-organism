/* osx-symbios smoke test (pure Node, no DOM) */
const fs = require('fs');
const vm = require('vm');

function makeCtx() {
  // minimal DOM stubs
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

console.log('=== osx-symbios-v0.1 smoke ===\n');

// 1) Core
console.log('[1] osx-core.js');
let ctx = load(['../web/osx-core.js']);
let OSX = get(ctx, 'OSX');
assert(OSX, 'exports OSX namespace');
assert(OSX.ORGANS.length === 12, '12 constitutional organs');
assert(OSX.PHYSICS.length === 3, '3 constitutional physics');
assert(OSX.INVARIANTS.length === 8, '8 invariants I1..I8');
assert(OSX.NOTEBOOKS.length === 6, '6 initial notebooks');
assert(OSX.MMNB_LINEAGE.length === 4, '4 MMNBs in cross-run lineage');
assert(OSX.REGISTRY.length >= 8, 'registry has >=8 entries');
assert(OSX.omegaScore(0.92, 21.91, 4.0, 0.78, 0.85) > 0.78, 'Ω canonical > 0.78');
assert(OSX.omegaScore(0.92, 21.91, 4.0, 0.78, 0.85) < 0.85, 'Ω canonical < 0.85');
const mnb = OSX.SAMPLE_MNB;
const rho = mnb.psi * mnb.tau / mnb.cost;
assert(Math.abs(rho - 0.682) < 0.01, '5-tuple MNB ρ ≈ 0.682');
assert(mnb.h.startsWith('h-'), 'MNB hash starts with h-');

// 2) Figure Lab
console.log('\n[2] osx-figure-lab.js');
ctx = load(['../web/osx-core.js', '../web/osx-figure-lab.js']);
OSX = get(ctx, 'OSX');
const FL = get(ctx, 'OSX_FIGURE_LAB');
assert(FL, 'exports OSX_FIGURE_LAB');
const fbd = FL.render('FREE_BODY_DIAGRAM', '30°');
assert(fbd.includes('<svg'), 'FREE_BODY_DIAGRAM returns SVG');
assert(fbd.includes('30'), 'includes angle 30');
const plot = FL.render('PLOT_2D', 'sin');
assert(plot.includes('<svg'), 'PLOT_2D returns SVG');
const flow = FL.render('FLOWCHART', '');
assert(flow.includes('MMNB'), 'FLOWCHART includes MMNB');
const arch = FL.render('SYSTEM_ARCHITECTURE', '');
assert(arch.includes('INFORMATIONAL'), 'SYSTEM_ARCH includes 3 planes');
const valOk = FL.validate({structure:1,labels:1,units:1,axes:1,nohallucination:1});
assert(valOk.status === 'PASS_VALIDATED', 'all-checks-pass → PASS_VALIDATED');
const valFail = FL.validate({structure:1,labels:0,units:0,axes:1,nohallucination:1});
assert(valFail.status === 'HOLD_LABEL_REVIEW', '2-failed → HOLD_LABEL_REVIEW');

// 3) Organism
console.log('\n[3] osx-organism.js');
ctx = load(['../web/osx-core.js', '../web/osx-organism.js']);
OSX = get(ctx, 'OSX');
const ORG = get(ctx, 'OSX_ORGANISM');
assert(ORG, 'exports OSX_ORGANISM');
const run = ORG.run('Should we adopt an offline CLI?');
assert(run.steps.length >= 8, 'run produces >= 8 steps');
assert(run.mmnb.length === 2, 'genesis + 1 child MMNB');
assert(run.final.omega > 0 && run.final.omega <= 1, 'Ω in [0,1]');
const o2 = ORG.recalcOmega(21.91);
assert(o2 > 0.78 && o2 < 0.85, 'recalcOmega(21.91) is in canonical range');
const m = ORG.newMMNB();
assert(m.h.startsWith('h-'), 'newMMNB has h- hash');

// 4) Combined
console.log('\n[4] combined load');
ctx = load(['../web/osx-core.js', '../web/osx-figure-lab.js', '../web/osx-organism.js', '../web/osx-canvas.js']);
assert(get(ctx, 'OSX'), 'OSX loaded');
assert(get(ctx, 'OSX_FIGURE_LAB'), 'OSX_FIGURE_LAB loaded');
assert(get(ctx, 'OSX_ORGANISM'), 'OSX_ORGANISM loaded');
assert(get(ctx, 'OSX_CANVAS'), 'OSX_CANVAS loaded');

console.log('\n=== ALL SMOKE TESTS PASS ===');
