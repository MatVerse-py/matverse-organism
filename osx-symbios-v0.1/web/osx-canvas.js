/* =================================================================
   osx-canvas.js  ·  Cognitive Canvas (pan/zoom node editor)
   - shapes by epistemic state: circle/diamond/hex/rect/...
   - tool: select / add-hyp / add-exp / add-evi / add-src / connect / delete
   - per-shape color and gate state
   ================================================================= */
(function (global) {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const initialState = () => ({
    nodes: [
      { id: "H1", x: 240, y: 220, shape: "hexagon",     label: "Adaptive routing reduces QBER", epistemic: "HYP" },
      { id: "H2", x: 460, y: 200, shape: "rect",        label: "IIRQ+ measurement",            epistemic: "EVD" },
      { id: "H3", x: 700, y: 220, shape: "rect-bold",   label: "MNB-Q adopted",                  epistemic: "ADM" },
      { id: "E1", x: 460, y: 360, shape: "circle",      label: "experimental run #47",           epistemic: "OBS" },
      { id: "S1", x: 220, y: 360, shape: "diamond",     label: "AGIS-IV 2026",                   epistemic: "INF" },
    ],
    edges: [
      { from: "H1", to: "H2", kind: "supports" },
      { from: "H1", to: "E1", kind: "tested_by" },
      { from: "E1", to: "H2", kind: "supports" },
      { from: "S1", to: "H1", kind: "cites" },
      { from: "H2", to: "H3", kind: "supersedes" },
    ],
  });

  let state = initialState();
  let view = { x: 0, y: 0, scale: 1.0 };
  let tool = "select";
  let connectFrom = null;
  let selectedId = null;
  let drag = null;

  const EP = global.OSX.EPISTEMIC_COLOR;
  const GLY = global.OSX.EPISTEMIC_GLYPH;

  // ------------------- shape renderers -------------------
  function drawShape(node, x, y) {
    const color = EP[node.epistemic] || "#7a8290";
    const label = node.label || node.id;
    const w = 110, h = 56;
    switch (node.shape) {
      case "circle":
        return `<g><circle cx="${x}" cy="${y}" r="34" fill="${color}" fill-opacity=".18" stroke="${color}" stroke-width="1.4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "diamond":
        return `<g><polygon points="${x},${y - 32} ${x + 50},${y} ${x},${y + 32} ${x - 50},${y}" fill="${color}" fill-opacity=".18" stroke="${color}" stroke-width="1.4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "hexagon": {
        const a = w / 2, b = h / 2, c = 16;
        return `<g><polygon points="${x - a + c},${y - b} ${x + a - c},${y - b} ${x + a},${y} ${x + a - c},${y + b} ${x - a + c},${y + b} ${x - a},${y}" fill="${color}" fill-opacity=".18" stroke="${color}" stroke-width="1.4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      }
      case "rect":
        return `<g><rect x="${x - a}" y="${y - b}" width="${w}" height="${h}" fill="${color}" fill-opacity=".18" stroke="${color}" stroke-width="1.4" rx="4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "rect-bold":
        return `<g><rect x="${x - a - 3}" y="${y - b - 3}" width="${w + 6}" height="${h + 6}" fill="${color}" fill-opacity=".32" stroke="${color}" stroke-width="2" rx="4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "circle-bold":
        return `<g><circle cx="${x}" cy="${y}" r="38" fill="${color}" fill-opacity=".32" stroke="${color}" stroke-width="2.4"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="700" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "diamond-blink":
        return `<g><polygon points="${x},${y - 32} ${x + 50},${y} ${x},${y + 32} ${x - 50},${y}" fill="${color}" fill-opacity=".32" stroke="${color}" stroke-width="2" stroke-dasharray="4 2">
                <animate attributeName="stroke-dashoffset" values="0;12" dur="0.8s" repeatCount="indefinite"/></polygon>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="700" fill="#e7ecf3">${node.id}</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${label.slice(0, 14)}</text></g>`;
      case "block":
      default:
        return `<g><rect x="${x - a}" y="${y - b}" width="${w}" height="${h}" fill="#3a3a3a" stroke="#c44b4b" stroke-width="2" rx="4" stroke-dasharray="4 3"/>
                <text x="${x}" y="${y - 4}" text-anchor="middle" font-size="12" font-weight="600" fill="#c44b4b">BLOCKED</text>
                <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" fill="#b6bdc8">${node.id}</text></g>`;
    }
    const a = w / 2, b = h / 2;
  }

  // ------------------- SVG render -------------------
  function render() {
    const svg = document.getElementById("cc-svg");
    if (!svg) return;
    const W = svg.clientWidth || 1200, H = svg.clientHeight || 700;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const edges = state.edges.map((e) => {
      const a = state.nodes.find((n) => n.id === e.from);
      const b = state.nodes.find((n) => n.id === e.to);
      if (!a || !b) return "";
      const color = EP[a.epistemic] || "#7a8290";
      return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="${color}" stroke-width="1.4" stroke-dasharray="${e.kind === "supersedes" ? "6 3" : "0"}" marker-end="url(#cc-arrow)"/>
              <text x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 4}" text-anchor="middle" font-size="9" fill="#7a8290">${e.kind}</text>`;
    }).join("");
    const nodes = state.nodes.map((n) => {
      const isSel = (n.id === selectedId) ? ' stroke-width="3" filter="url(#cc-glow)"' : "";
      return drawShape(n, n.x, n.y).replace("<g>", `<g data-node-id="${n.id}"${isSel}>`);
    }).join("");
    svg.innerHTML = `
      <defs>
        <marker id="cc-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#7a8290"/>
        </marker>
        <filter id="cc-glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <g transform="translate(${view.x} ${view.y}) scale(${view.scale})">${edges}${nodes}</g>
    `;
  }

  // ------------------- tool actions -------------------
  function setTool(t) {
    tool = t;
    document.querySelectorAll(".osx-cc-tools button[data-cc-tool]").forEach((b) => b.classList.toggle("is-active", b.dataset.ccTool === t));
    const svg = document.getElementById("cc-svg");
    if (svg) svg.style.cursor = (t === "select" || t === "connect") ? "default" : "crosshair";
  }

  function addNode(kind) {
    const shape = GLY[kind === "hyp" ? "HYP" : kind === "exp" ? "OBS" : kind === "evi" ? "EVD" : "INF"];
    const next = state.nodes.length === 0 ? "N1" : "N" + (state.nodes.length + 1);
    const epistemic = kind === "hyp" ? "HYP" : kind === "exp" ? "OBS" : kind === "evi" ? "EVD" : "INF";
    const label = kind === "hyp" ? "nova hipótese" : kind === "exp" ? "novo experimento" : kind === "evi" ? "nova evidência" : "nova fonte";
    state.nodes.push({ id: next, x: 400 + (Math.random() - 0.5) * 80, y: 250 + (Math.random() - 0.5) * 60, shape, label, epistemic });
    selectedId = next;
    render();
  }

  function deleteSelected() {
    if (!selectedId) return;
    state.nodes = state.nodes.filter((n) => n.id !== selectedId);
    state.edges = state.edges.filter((e) => e.from !== selectedId && e.to !== selectedId);
    selectedId = null;
    render();
  }

  // ------------------- event handlers -------------------
  function bind() {
    const svg = document.getElementById("cc-svg");
    if (!svg) return;
    svg.addEventListener("mousedown", (e) => {
      const pt = svgPoint(svg, e);
      const n = pickNode(pt);
      if (tool === "add-hyp" || tool === "add-exp" || tool === "add-evi" || tool === "add-src") {
        const kind = tool.split("-")[1];
        const shape = GLY[kind === "hyp" ? "HYP" : kind === "exp" ? "OBS" : kind === "evi" ? "EVD" : "INF"];
        const epistemic = kind === "hyp" ? "HYP" : kind === "exp" ? "OBS" : kind === "evi" ? "EVD" : "INF";
        const label = kind === "hyp" ? "nova hipótese" : kind === "exp" ? "novo experimento" : kind === "evi" ? "nova evidência" : "nova fonte";
        const id = "N" + (state.nodes.length + 1);
        state.nodes.push({ id, x: pt.x, y: pt.y, shape, label, epistemic });
        selectedId = id;
        render();
        return;
      }
      if (tool === "delete" && n) {
        selectedId = n.id;
        deleteSelected();
        return;
      }
      if (tool === "connect") {
        if (n) {
          if (!connectFrom) connectFrom = n.id;
          else {
            state.edges.push({ from: connectFrom, to: n.id, kind: "supports" });
            connectFrom = null;
            render();
          }
        }
        return;
      }
      // default: select / drag
      if (n) {
        selectedId = n.id;
        drag = { id: n.id, dx: pt.x - n.x, dy: pt.y - n.y };
        render();
      } else {
        selectedId = null;
        render();
      }
    });
    svg.addEventListener("mousemove", (e) => {
      if (!drag) return;
      const pt = svgPoint(svg, e);
      const n = state.nodes.find((x) => x.id === drag.id);
      if (n) { n.x = pt.x - drag.dx; n.y = pt.y - drag.dy; render(); }
    });
    svg.addEventListener("mouseup", () => { drag = null; });
    document.querySelectorAll(".osx-cc-tools button[data-cc-tool]").forEach((b) => b.addEventListener("click", () => setTool(b.dataset.ccTool)));
    document.getElementById("cc-export").addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "cognitive-canvas.json";
      a.click();
    });
    document.getElementById("cc-import").addEventListener("click", () => {
      const inp = document.createElement("input");
      inp.type = "file"; inp.accept = "application/json";
      inp.onchange = () => {
        const f = inp.files[0]; if (!f) return;
        const r = new FileReader();
        r.onload = () => { try { state = JSON.parse(r.result); render(); } catch (e) { alert("JSON inválido"); } };
        r.readAsText(f);
      };
      inp.click();
    });
  }

  function svgPoint(svg, e) {
    const rect = svg.getBoundingClientRect();
    return { x: (e.clientX - rect.left - view.x) / view.scale, y: (e.clientY - rect.top - view.y) / view.scale };
  }

  function pickNode(p) {
    for (let i = state.nodes.length - 1; i >= 0; i--) {
      const n = state.nodes[i];
      if (Math.abs(p.x - n.x) < 60 && Math.abs(p.y - n.y) < 30) return n;
    }
    return null;
  }

  function init() {
    bind();
    render();
  }

  global.OSX_CANVAS = { init, render, setTool, addNode, deleteSelected, getState: () => state, reset: () => { state = initialState(); render(); } };
})(window);
