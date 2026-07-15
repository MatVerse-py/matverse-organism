/* =================================================================
   osx-figure-lab.js  ·  SVG renderers by category
   Deterministic per category — no generative model for technical figures.
   Each renderer returns a full <svg> string for the requested spec.
   ================================================================= */
(function (global) {
  "use strict";

  const W = 800, H = 500;
  const svgOpen = (inner) =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="Helvetica, Arial, sans-serif">${inner}</svg>`;
  const esc = (s) => String(s).replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]));

  // ---------------------- FREE BODY DIAGRAM ----------------------
  function freeBody(promptText) {
    // parse a few keywords to choose an angle / set
    let angle = 30;
    const m = /(\d+)\s*°/.exec(promptText || "");
    if (m) angle = Math.max(5, Math.min(80, parseInt(m[1], 10)));
    const rad = (angle * Math.PI) / 180;
    const x0 = 400, y0 = 260, W0 = 180, H0 = 90;
    const sinA = Math.sin(rad), cosA = Math.cos(rad);
    // block on inclined plane
    const inclinePath = `M ${x0 - 240} ${y0 + 60} L ${x0 + 280} ${y0 + 60 - 280 * Math.tan(rad)} L ${x0 + 280} ${y0 + 60} Z`;
    return svgOpen(`
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#1a1a1a"/>
        </marker>
        <pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="#bbb" stroke-width="1"/>
        </pattern>
      </defs>
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">Diagrama de corpo livre · ${esc(promptText || "plano inclinado a 30°")}</text>
      <text x="20" y="48" font-size="10" fill="#666">FREE_BODY_DIAGRAM · SVG · ${angle}°</text>

      <!-- incline -->
      <path d="${inclinePath}" fill="url(#hatch)" stroke="#666" stroke-width="1"/>
      <line x1="${x0 - 240}" y1="${y0 + 60}" x2="${x0 + 280}" y2="${y0 + 60 - 280 * Math.tan(rad)}"
            stroke="#666" stroke-width="1.5"/>
      <!-- block -->
      <g transform="translate(${x0 - W0 / 2} ${y0 - H0 - 60 * Math.tan(rad)}) rotate(${-angle} ${W0 / 2} ${H0 / 2})">
        <rect width="${W0}" height="${H0}" fill="#cfe2ff" stroke="#1a1a1a" stroke-width="1.5" rx="4"/>
        <text x="${W0 / 2}" y="${H0 / 2 + 5}" text-anchor="middle" font-size="14" fill="#1a1a1a">m</text>
      </g>
      <!-- vectors from block center -->
      <g transform="translate(${x0} ${y0 - H0 / 2 - 60 * Math.tan(rad)})">
        <!-- weight mg (down) -->
        <line x1="0" y1="0" x2="0" y2="100" stroke="#1a1a1a" stroke-width="1.8" marker-end="url(#arr)"/>
        <text x="6" y="105" font-size="12" fill="#1a1a1a">mg</text>
        <!-- normal N (perpendicular to plane, away from plane) -->
        <line x1="0" y1="0" x2="${-100 * sinA}" y2="${-100 * cosA}" stroke="#1a1a1a" stroke-width="1.8" marker-end="url(#arr)"/>
        <text x="${-110 * sinA - 16}" y="${-100 * cosA - 4}" font-size="12" fill="#1a1a1a">N</text>
        <!-- friction f (up the plane, opposes motion) -->
        <line x1="0" y1="0" x2="${120 * cosA}" y2="${-120 * sinA}" stroke="#1a1a1a" stroke-width="1.8" marker-end="url(#arr)"/>
        <text x="${125 * cosA}" y="${-120 * sinA - 4}" font-size="12" fill="#1a1a1a">f</text>
      </g>
      <!-- angle marker -->
      <path d="M ${x0 - 240 + 60} ${y0 + 60} A 60 60 0 0 0 ${x0 - 240 + 60 * Math.cos(-rad)} ${y0 + 60 + 60 * Math.sin(-rad)}"
            fill="none" stroke="#1a1a1a" stroke-width="1"/>
      <text x="${x0 - 240 + 70}" y="${y0 + 60 - 10}" font-size="12" fill="#1a1a1a">${angle}°</text>
    `);
  }

  // ---------------------- PLOT 2D ----------------------
  function plot2d(promptText) {
    // generate a sample function plot
    const xs = [], ys = [];
    for (let i = 0; i <= 80; i++) {
      const x = (i / 80) * 2 * Math.PI;
      xs.push(x);
      ys.push(Math.sin(x) * Math.exp(-x / 8));
    }
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const xMin = 0, xMax = 2 * Math.PI;
    const padL = 60, padR = 20, padT = 50, padB = 50;
    const px = (x) => padL + ((x - xMin) / (xMax - xMin)) * (W - padL - padR);
    const py = (y) => padT + (1 - (y - minY) / (maxY - minY || 1)) * (H - padT - padB);
    let path = "";
    xs.forEach((x, i) => { path += (i ? " L" : "M") + " " + px(x) + " " + py(ys[i]); });
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">PLOT_2D · ${esc(promptText || "sin(x)·exp(-x/8)")}</text>
      <text x="20" y="48" font-size="10" fill="#666">DATA_VISUALIZATION</text>
      <!-- axes -->
      <line x1="${padL}" y1="${H - padB}" x2="${W - padR}" y2="${H - padB}" stroke="#1a1a1a" stroke-width="1"/>
      <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${H - padB}" stroke="#1a1a1a" stroke-width="1"/>
      <!-- x ticks -->
      ${[0, Math.PI / 2, Math.PI, 3 * Math.PI / 2, 2 * Math.PI].map((t) => `
        <line x1="${px(t)}" y1="${H - padB}" x2="${px(t)}" y2="${H - padB + 4}" stroke="#1a1a1a"/>
        <text x="${px(t)}" y="${H - padB + 16}" text-anchor="middle" font-size="10" fill="#1a1a1a">${(t / Math.PI).toFixed(1)}π</text>
      `).join("")}
      <!-- y ticks -->
      ${[minY, (minY + maxY) / 2, maxY].map((t) => `
        <line x1="${padL - 4}" y1="${py(t)}" x2="${padL}" y2="${py(t)}" stroke="#1a1a1a"/>
        <text x="${padL - 8}" y="${py(t) + 3}" text-anchor="end" font-size="10" fill="#1a1a1a">${t.toFixed(2)}</text>
      `).join("")}
      <text x="${W / 2}" y="${H - 12}" text-anchor="middle" font-size="11" fill="#1a1a1a">x</text>
      <text x="14" y="${H / 2}" text-anchor="middle" font-size="11" fill="#1a1a1a" transform="rotate(-90 14 ${H / 2})">y</text>
      <!-- function -->
      <path d="${path}" fill="none" stroke="#1a66d6" stroke-width="2"/>
      <text x="${px(Math.PI)}" y="${py(Math.exp(-Math.PI / 8)) - 8}" text-anchor="middle" font-size="11" fill="#1a66d6">y = sin(x)·exp(-x/8)</text>
    `);
  }

  // ---------------------- FLOWCHART ----------------------
  function flowchart(promptText) {
    const nodes = [
      { id: "PROB",  label: "Problem",       x: 100, y: 240, w: 130, h: 50, color: "#cfe2ff" },
      { id: "MMNB",  label: "MMNB",          x: 290, y: 240, w: 110, h: 50, color: "#d8f0d8" },
      { id: "COG",   label: "COG",           x: 460, y: 240, w: 100, h: 50, color: "#fff4c2" },
      { id: "GATE",  label: "Ω-Gate",        x: 620, y: 240, w: 110, h: 50, color: "#ffd6c2" },
      { id: "RUN",   label: "Run",           x: 620, y: 350, w: 110, h: 50, color: "#d8f0d8" },
      { id: "MMNB2", label: "new MMNB",      x: 460, y: 350, w: 120, h: 50, color: "#d8f0d8" },
    ];
    const edges = [
      ["PROB", "MMNB"], ["MMNB", "COG"], ["COG", "GATE"], ["GATE", "RUN"], ["RUN", "MMNB2"], ["MMNB2", "MMNB"],
    ];
    return svgOpen(`
      <defs><marker id="farr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="#1a1a1a"/></marker></defs>
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">FLOWCHART · MatVerse Organism cycle</text>
      <text x="20" y="48" font-size="10" fill="#666">${esc(promptText || "Problem → MMNB → COG → Ω-Gate → Run → new MMNB")}</text>
      ${edges.map(([a, b]) => {
        const A = nodes.find((n) => n.id === a), B = nodes.find((n) => n.id === b);
        return `<line x1="${A.x + A.w}" y1="${A.y + A.h / 2}" x2="${B.x}" y2="${B.y + B.h / 2}"
                  stroke="#1a1a1a" stroke-width="1.2" marker-end="url(#farr)"/>`;
      }).join("")}
      ${nodes.map((n) => `
        <g>
          <rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" fill="${n.color}" stroke="#1a1a1a" stroke-width="1" rx="4"/>
          <text x="${n.x + n.w / 2}" y="${n.y + n.h / 2 + 4}" text-anchor="middle" font-size="12" fill="#1a1a1a">${n.label}</text>
        </g>
      `).join("")}
    `);
  }

  // ---------------------- NETWORK GRAPH ----------------------
  function networkGraph() {
    const nodes = [
      { id: "OSX",   x: 400, y: 100, r: 32, label: "OSX", color: "#5fd2a4" },
      { id: "SYM",   x: 200, y: 200, r: 28, label: "SymbiOS", color: "#d6c25a" },
      { id: "CAS",   x: 600, y: 200, r: 28, label: "Cassandra", color: "#d6c25a" },
      { id: "URA",   x: 100, y: 350, r: 28, label: "URANO", color: "#d97757" },
      { id: "ATL",   x: 300, y: 380, r: 28, label: "Atlas", color: "#5fd2a4" },
      { id: "ORG",   x: 500, y: 380, r: 28, label: "Organism", color: "#d6c25a" },
      { id: "HUMAN", x: 700, y: 350, r: 32, label: "Human", color: "#5a8dee" },
    ];
    const edges = [["OSX","SYM"],["OSX","CAS"],["SYM","URA"],["SYM","ATL"],["SYM","ORG"],["CAS","ORG"],["ORG","ATL"],["ORG","HUMAN"],["ATL","HUMAN"]];
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">NETWORK_GRAPH · MatVerse topology</text>
      <text x="20" y="48" font-size="10" fill="#666">OSX ↔ SymbiOS ↔ URANO/Atlas/Organism ↔ Human</text>
      ${edges.map(([a, b]) => {
        const A = nodes.find((n) => n.id === a), B = nodes.find((n) => n.id === b);
        return `<line x1="${A.x}" y1="${A.y}" x2="${B.x}" y2="${B.y}" stroke="#666" stroke-width="1.2"/>`;
      }).join("")}
      ${nodes.map((n) => `
        <g>
          <circle cx="${n.x}" cy="${n.y}" r="${n.r}" fill="${n.color}" stroke="#1a1a1a" stroke-width="1.2"/>
          <text x="${n.x}" y="${n.y + 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#1a1a1a">${n.label}</text>
        </g>
      `).join("")}
    `);
  }

  // ---------------------- CONCEPT MAP ----------------------
  function conceptMap() {
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">CONCEPT_MAP · Triadic organization</text>
      <text x="20" y="48" font-size="10" fill="#666">INFORMATIONAL · DIGITAL · PHYSICAL</text>
      <g>
        <line x1="400" y1="100" x2="200" y2="380" stroke="#5fd2a4" stroke-width="1.2"/>
        <line x1="400" y1="100" x2="400" y2="400" stroke="#d6c25a" stroke-width="1.2"/>
        <line x1="400" y1="100" x2="600" y2="380" stroke="#d97757" stroke-width="1.2"/>
        <circle cx="400" cy="100" r="40" fill="#fff4c2" stroke="#1a1a1a" stroke-width="1.4"/>
        <text x="400" y="105" text-anchor="middle" font-size="13" font-weight="700" fill="#1a1a1a">MatVerse</text>
        <text x="400" y="120" text-anchor="middle" font-size="9" fill="#666">triadic</text>
        <circle cx="200" cy="380" r="36" fill="#d8f0d8" stroke="#5fd2a4" stroke-width="1.4"/>
        <text x="200" y="378" text-anchor="middle" font-size="12" font-weight="700" fill="#1a1a1a">Informational</text>
        <text x="200" y="392" text-anchor="middle" font-size="9" fill="#1a1a1a">MMNB · lineage · claims</text>
        <circle cx="400" cy="400" r="36" fill="#fff4c2" stroke="#d6c25a" stroke-width="1.4"/>
        <text x="400" y="398" text-anchor="middle" font-size="12" font-weight="700" fill="#1a1a1a">Digital</text>
        <text x="400" y="412" text-anchor="middle" font-size="9" fill="#1a1a1a">programs · skills · Ω-Gate</text>
        <circle cx="600" cy="380" r="36" fill="#ffd6c2" stroke="#d97757" stroke-width="1.4"/>
        <text x="600" y="378" text-anchor="middle" font-size="12" font-weight="700" fill="#1a1a1a">Physical</text>
        <text x="600" y="392" text-anchor="middle" font-size="9" fill="#1a1a1a">humans · machines · nodes</text>
      </g>
    `);
  }

  // ---------------------- TIMELINE ----------------------
  function timeline() {
    const events = [
      { v: "v3.0.0",  x: 80,  t: "46 testes · HypothesisOps wedge" },
      { v: "v3.6.0",  x: 240, t: "116 testes · 8+1 órgãos" },
      { v: "v3.7.0",  x: 400, t: "146 testes · MMNB + Capability + Probes" },
      { v: "v3.8.0",  x: 560, t: "253 testes · GTHDL + 5-tuple + Manifold" },
      { v: "v0.1",    x: 720, t: "OSX + SymbiOS Network Notebook" },
    ];
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">TIMELINE · MatVerse evolution</text>
      <text x="20" y="48" font-size="10" fill="#666">v3.0.0 → v3.8.0 → OSX v0.1</text>
      <line x1="40" y1="260" x2="${W - 40}" y2="260" stroke="#1a1a1a" stroke-width="1.6"/>
      ${events.map((e) => `
        <g>
          <circle cx="${e.x}" cy="260" r="9" fill="#5a8dee" stroke="#1a1a1a"/>
          <text x="${e.x}" y="240" text-anchor="middle" font-size="13" font-weight="600" fill="#1a1a1a">${e.v}</text>
          <text x="${e.x}" y="290" text-anchor="middle" font-size="10" fill="#1a1a1a">${e.t}</text>
        </g>
      `).join("")}
    `);
  }

  // ---------------------- SYSTEM ARCHITECTURE ----------------------
  function systemArch() {
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">SYSTEM_ARCHITECTURE · 12 órgãos + 3 física</text>
      <text x="20" y="48" font-size="10" fill="#666">3 planos · 1 ciclo · 1 gate</text>
      ${["INFORMATIONAL","DIGITAL","PHYSICAL"].map((p, i) => `
        <g>
          <rect x="${40 + i * 250}" y="100" width="220" height="350" fill="${
            p === "INFORMATIONAL" ? "#d8f0d8" : p === "DIGITAL" ? "#fff4c2" : "#ffd6c2"
          }" stroke="#1a1a1a" stroke-width="1" rx="6"/>
          <text x="${150 + i * 250}" y="125" text-anchor="middle" font-size="13" font-weight="700" fill="#1a1a1a">${p}</text>
          <text x="${150 + i * 250}" y="142" text-anchor="middle" font-size="9" fill="#666">${i === 0 ? "rede" : i === 1 ? "programação" : "sistema"}</text>
          ${["MMNB", "Atlas", "Registry", "Evidence", "MNB lineage", "claims"].slice(0, i === 0 ? 6 : 3)
            .map((label, j) => `<text x="${60 + i * 250}" y="${175 + j * 32}" font-size="11" fill="#1a1a1a">• ${label}</text>`).join("")}
          ${i === 0 ? `
            <text x="60" y="380" font-size="11" fill="#1a1a1a">• Paper Vivo</text>
            <text x="60" y="412" font-size="11" fill="#1a1a1a">• Deep Research</text>
          ` : ""}
          ${i === 1 ? `
            <text x="310" y="280" font-size="11" fill="#1a1a1a">• Cassandra</text>
            <text x="310" y="312" font-size="11" fill="#1a1a1a">• URANO</text>
            <text x="310" y="344" font-size="11" fill="#1a1a1a">• Ω-Gate</text>
            <text x="310" y="376" font-size="11" fill="#1a1a1a">• EvidenceOS</text>
          ` : ""}
          ${i === 2 ? `
            <text x="560" y="280" font-size="11" fill="#1a1a1a">• Human Node</text>
            <text x="560" y="312" font-size="11" fill="#1a1a1a">• SymbiOS Edge</text>
            <text x="560" y="344" font-size="11" fill="#1a1a1a">• Twin Server</text>
            <text x="560" y="376" font-size="11" fill="#1a1a1a">• Sensors</text>
          ` : ""}
        </g>
      `).join("")}
    `);
  }

  // ---------------------- DEFAULT / FALLBACK ----------------------
  function fallback(category) {
    return svgOpen(`
      <rect width="${W}" height="${H}" fill="#ffffff"/>
      <text x="20" y="30" font-size="14" font-weight="600" fill="#1a1a1a">${category}</text>
      <text x="20" y="48" font-size="10" fill="#666">renderizador específico não implementado nesta release</text>
      <text x="${W / 2}" y="${H / 2 - 8}" text-anchor="middle" font-size="14" fill="#666">${category}</text>
      <text x="${W / 2}" y="${H / 2 + 12}" text-anchor="middle" font-size="11" fill="#999">renderer pending · contribute via PR</text>
    `);
  }

  // ---------------------- ROUTER ----------------------
  function render(category, prompt) {
    switch (category) {
      case "FREE_BODY_DIAGRAM":  return freeBody(prompt);
      case "PLOT_2D":            return plot2d(prompt);
      case "FLOWCHART":          return flowchart(prompt);
      case "NETWORK_GRAPH":      return networkGraph();
      case "CONCEPT_MAP":        return conceptMap();
      case "TIMELINE":           return timeline();
      case "SYSTEM_ARCHITECTURE": return systemArch();
      default:                   return fallback(category);
    }
  }

  // ---------------------- VISUAL Ω-GATE ----------------------
  function validate(checks) {
    const missing = Object.keys(checks).filter((k) => !checks[k]);
    if (missing.length === 0) return { status: "PASS_VALIDATED", missing: [] };
    if (missing.length <= 2)  return { status: "HOLD_LABEL_REVIEW", missing };
    return { status: "FAIL_STRUCTURAL", missing };
  }

  global.OSX_FIGURE_LAB = { render, validate };
})(window);
