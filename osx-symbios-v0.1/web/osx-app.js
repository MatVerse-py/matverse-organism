/* =================================================================
   osx-app.js  ·  app bootstrap
   Wires the views, top bar, dock, and the organ/registry renderers.
   ================================================================= */
(function (global) {
  "use strict";
  const OSX = global.OSX;

  // ---------------------- Constellation SVG ----------------------
  function renderConstellation() {
    const svg = document.getElementById("osx-constellation-svg");
    if (!svg) return;
    const W = svg.clientWidth || 1100, H = svg.clientHeight || 600;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    // build a 6-node constellation + hub + 3-physics satellites
    const hub = { x: W / 2, y: H / 2, r: 64, label: "MatVerse OSX v0.1", color: "#5a8dee" };
    const nodes = [
      { id: "OSX",      x: hub.x,        y: hub.y - 200, r: 36, label: "OSX",         color: "#5fd2a4" },
      { id: "SYMB",     x: hub.x - 280,  y: hub.y - 70,  r: 32, label: "SymbiOS",     color: "#d6c25a" },
      { id: "CASS",     x: hub.x + 280,  y: hub.y - 70,  r: 32, label: "Cassandra",   color: "#d6c25a" },
      { id: "URANO",    x: hub.x - 360,  y: hub.y + 110, r: 30, label: "URANO",       color: "#d97757" },
      { id: "ATLAS",    x: hub.x - 100,  y: hub.y + 200, r: 30, label: "Atlas",       color: "#5fd2a4" },
      { id: "ORG",      x: hub.x + 100,  y: hub.y + 200, r: 30, label: "Organism",    color: "#d6c25a" },
      { id: "HUMAN",    x: hub.x + 360,  y: hub.y + 110, r: 36, label: "Human Node",  color: "#5a8dee" },
    ];
    const physics = [
      { x: hub.x - 480, y: hub.y + 0,   label: "GTHDL",  color: "#5fd2a4" },
      { x: hub.x + 480, y: hub.y + 0,   label: "Riemann", color: "#d6c25a" },
      { x: hub.x + 0,   y: hub.y + 320, label: "Epistemic", color: "#d97757" },
    ];
    const edges = [
      ["OSX", "SYMB"], ["OSX", "CASS"], ["OSX", "ORG"], ["OSX", "ATLAS"],
      ["SYMB", "URANO"], ["SYMB", "ORG"], ["CASS", "ORG"],
      ["ORG", "ATLAS"], ["ORG", "HUMAN"], ["ATLAS", "HUMAN"],
    ];
    const edge = (a, b) => `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#3a4350" stroke-width="1.2" stroke-dasharray="2 3"/>`;
    const ring = (cx, cy, r, c) => `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${c}" fill-opacity="0.06" stroke="${c}" stroke-width="1" stroke-dasharray="3 3"/>`;
    const orbits = [
      ring(hub.x, hub.y, 220, "#5a8dee"),
      ring(hub.x, hub.y, 320, "#5fd2a4"),
      ring(hub.x, hub.y, 420, "#d6c25a"),
    ];
    const nodeG = nodes.map((n) => `
      <g>
        <circle cx="${n.x}" cy="${n.y}" r="${n.r}" fill="${n.color}" fill-opacity="0.18" stroke="${n.color}" stroke-width="1.5"/>
        <text x="${n.x}" y="${n.y + 4}" text-anchor="middle" font-size="11" font-weight="600" fill="#e7ecf3">${n.label}</text>
      </g>`).join("");
    const physicsG = physics.map((p) => `
      <g>
        <rect x="${p.x - 50}" y="${p.y - 18}" width="100" height="36" rx="6" fill="${p.color}" fill-opacity="0.10" stroke="${p.color}" stroke-width="1.4" stroke-dasharray="3 2"/>
        <text x="${p.x}" y="${p.y + 4}" text-anchor="middle" font-size="11" font-weight="600" fill="#e7ecf3">${p.label}</text>
      </g>`).join("");
    const edgesG = edges.map(([a, b]) => {
      const A = nodes.find((n) => n.label.toLowerCase().startsWith(a.toLowerCase())) || nodes.find((n) => n.id === a);
      const B = nodes.find((n) => n.label.toLowerCase().startsWith(b.toLowerCase())) || nodes.find((n) => n.id === b);
      return A && B ? edge(A, B) : "";
    }).join("");
    svg.innerHTML = `
      ${orbits.join("")}
      ${edgesG}
      <g>
        <circle cx="${hub.x}" cy="${hub.y}" r="${hub.r}" fill="${hub.color}" fill-opacity="0.18" stroke="${hub.color}" stroke-width="2"/>
        <text x="${hub.x}" y="${hub.y - 4}" text-anchor="middle" font-size="13" font-weight="700" fill="#e7ecf3">${hub.label}</text>
        <text x="${hub.x}" y="${hub.y + 14}" text-anchor="middle" font-size="10" fill="#b6bdc8">12 organs · 3 physics</text>
      </g>
      ${nodeG}
      ${physicsG}
    `;
  }

  // ---------------------- Notebook renderers ----------------------
  function renderNotebookList(filter) {
    const ul = document.getElementById("osx-nb-list");
    if (!ul) return;
    const q = (filter || "").toLowerCase();
    ul.innerHTML = "";
    OSX.NOTEBOOKS.forEach((nb) => {
      const matchingCells = q ? nb.cells.filter((c) => (c.claim || "").toLowerCase().includes(q)) : nb.cells;
      const li = document.createElement("li");
      li.dataset.notebookId = nb.id;
      li.innerHTML = `<b>${nb.title}</b><span class="epistemic">${nb.epistemic} · ${matchingCells.length} cells</span>`;
      li.onclick = () => openNotebook(nb.id);
      ul.appendChild(li);
    });
  }

  let currentNb = OSX.NOTEBOOKS[2]; // URANO by default
  function openNotebook(id) {
    currentNb = OSX.NOTEBOOKS.find((n) => n.id === id) || OSX.NOTEBOOKS[0];
    document.getElementById("osx-nb-title").textContent = currentNb.title;
    document.getElementById("osx-nb-meta").textContent = `${currentNb.id} · Gate: ${currentNb.epistemic}`;
    document.querySelectorAll("#osx-nb-list li").forEach((el) => el.classList.toggle("is-active", el.dataset.notebookId === id));
    renderCells();
  }

  function renderCells() {
    const wrap = document.getElementById("osx-nb-cells");
    if (!wrap) return;
    wrap.innerHTML = currentNb.cells.map((c) => `
      <article class="osx-cell" data-cell-id="${c.id}" data-epistemic="${c.epistemic}">
        <div class="head"><span>${c.id} · ${c.type}</span><span>${c.epistemic}</span></div>
        <div class="body">${c.claim}</div>
      </article>
    `).join("");
    wrap.querySelectorAll(".osx-cell").forEach((el) => el.addEventListener("click", () => selectCell(el.dataset.cellId)));
  }

  function selectCell(cellId) {
    const cell = currentNb.cells.find((c) => c.id === cellId);
    if (!cell) return;
    document.querySelectorAll("#osx-nb-cells .osx-cell").forEach((el) => el.classList.toggle("is-selected", el.dataset.cellId === cellId));
    // triadic inspector
    const info = document.getElementById("lens-informational");
    const digi = document.getElementById("lens-digital");
    const phys = document.getElementById("lens-physical");
    info.innerHTML = `<p><b>${cell.id}</b> · ${cell.type} · ${cell.epistemic}</p><pre>claim: ${cell.claim}
source_ids: [DOC-002, RUN-005]
lineage: parent = MMNB-${currentNb.id.slice(-3)}-parent
relations: supports CLM-${cell.id.slice(-3)}
epistemic_state: ${cell.epistemic}</pre>`;
    digi.innerHTML = `<pre>program_binding_id: PRG-${cell.id.slice(-3)}
runtime: PYTHON_STDLIB
entrypoint: experiments/${currentNb.id.toLowerCase()}.py
permissions:
  - read:notebook
  - write:results
network_access: false
execution_state: ${cell.epistemic === "CON" ? "FINALIZED" : "NOT_EXECUTED"}</pre>`;
    phys.innerHTML = `<pre>physical_ref: RUN-${cell.id.slice(-3)}
node_id: NODE-EDGE-001
node_type: CHROMEBOOK
operator: USER-001
telemetry_status: NOT_VALIDATED
network_state: LOCAL
started_at: 2026-07-15T11:30:00Z</pre>`;
  }

  // ---------------------- Cassandra command bar ----------------------
  function bindCassandra() {
    const input = document.getElementById("cassandra-cmd");
    const btn = document.getElementById("cassandra-run");
    const status = document.getElementById("cassandra-status");
    const handle = () => {
      const cmd = (input.value || "").trim();
      if (!cmd) return;
      // local rule-based dispatch
      const lower = cmd.toLowerCase();
      let note = "Cassandra local · demonstrativa · não-LLM";
      if (/^(crie|criar|nova?)\s+hip[oó]tese/.test(lower)) {
        const id = "CELL-" + String(100 + currentNb.cells.length).padStart(3, "0");
        currentNb.cells.push({ id, type: "HYPOTHESIS", epistemic: "HYP", claim: cmd.replace(/^crie\s+hip[oó]tese\s+/i, "") });
        note = `criou célula ${id} (HYP) em ${currentNb.title}`;
      } else if (/^(rode|rodar|run)/.test(lower)) {
        note = "URANO receberia esta ordem em produção (HOLD nesta release)";
      } else if (/^(explique|explain)/.test(lower)) {
        const sel = document.querySelector("#osx-nb-cells .osx-cell.is-selected");
        note = sel ? `explicando ${sel.dataset.cellId}… (HOLD · use a célula selecionada)` : "selecione uma célula antes de pedir explicação";
      } else if (lower === "omega" || /recalcular\s+omega/.test(lower)) {
        const o = global.OSX_ORGANISM.recalcOmega(21.91);
        note = `Ω recalculado = ${o.toFixed(4)} · VIABLE`;
        document.getElementById("osx-omega-value").textContent = o.toFixed(2);
      } else {
        note = `comando recebido: "${cmd}" · sem handler local (apenas roteamento demonstrativo)`;
      }
      status.textContent = note;
      renderCells();
      input.value = "";
    };
    btn.addEventListener("click", handle);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") handle(); });
  }

  // ---------------------- Atlas / Registry renderers ----------------------
  function renderAtlas() {
    const organs = document.getElementById("osx-atlas-organs");
    const physics = document.getElementById("osx-atlas-physics");
    if (orgs) orgs.innerHTML = "";
    if (organs) organs.innerHTML = OSX.ORGANS.map((o, i) => `<li><b>${i + 1}. ${o.id}</b> — ${o.role}</li>`).join("");
    if (physics) physics.innerHTML = OSX.PHYSICS.map((p) => `<li><b>${p.id}</b> — <code>${p.eq}</code></li>`).join("");
    const invs = document.getElementById("osx-atlas-invariants");
    if (invs) invs.innerHTML = OSX.INVARIANTS.map((s) => `<li>${s}</li>`).join("");
  }
  function renderRegistry() {
    const tbody = document.querySelector("#osx-registry tbody");
    if (!tbody) return;
    tbody.innerHTML = OSX.REGISTRY.map((r) => `
      <tr>
        <td><code>${r.id}</code></td>
        <td>${r.type}</td>
        <td>${r.desc}</td>
        <td><span class="osx-gate ${r.state === "ACTIVE" ? "is-pass" : r.state === "HOLD" ? "" : "is-esc"}">${r.state}</span></td>
      </tr>`).join("");
  }

  // ---------------------- Figure Lab bind ----------------------
  function bindFigureLab() {
    const cat = document.getElementById("fl-category");
    const style = document.getElementById("fl-style");
    const prompt = document.getElementById("fl-prompt");
    const gen = document.getElementById("fl-generate");
    const status = document.getElementById("fl-status");
    const svg = document.getElementById("fl-svg");
    const exp = document.getElementById("fl-export-svg");
    const checks = {};
    document.querySelectorAll(".osx-fl-checks input").forEach((cb) => checks[cb.dataset.check] = cb.checked);
    const collectChecks = () => {
      document.querySelectorAll(".osx-fl-checks input").forEach((cb) => checks[cb.dataset.check] = cb.checked);
      return checks;
    };
    const generate = () => {
      const c = cat.value, s = style.value, p = prompt.value;
      const result = global.OSX_FIGURE_LAB.render(c, p);
      svg.innerHTML = result.replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
      const v = global.OSX_FIGURE_LAB.validate(collectChecks());
      status.innerHTML = `categoria: <b>${c}</b> · estilo: <b>${s}</b> · Visual Ω-Gate: <span class="osx-gate ${v.status === "PASS_VALIDATED" ? "is-pass" : v.status === "HOLD_LABEL_REVIEW" ? "" : "is-esc"}">${v.status}</span>`;
      // also recompute the organism Ω
      const o = global.OSX_ORGANISM.recalcOmega(21.91);
      document.getElementById("osx-omega-value").textContent = o.toFixed(2);
    };
    gen.addEventListener("click", generate);
    exp.addEventListener("click", () => {
      const blob = new Blob([svg.outerHTML.replace(/<\/?svg[^>]*>/g, (m) => m)], { type: "image/svg+xml" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "figure.svg";
      a.click();
    });
    // initial render
    generate();
  }

  // ---------------------- Organism page bind ----------------------
  function bindOrganism() {
    const ta = document.getElementById("org-problem");
    const runBtn = document.getElementById("org-run");
    const omegaBtn = document.getElementById("org-omega");
    const mmnbBtn = document.getElementById("org-mmnb");
    const out = document.getElementById("org-out");
    runBtn.addEventListener("click", () => {
      const r = global.OSX_ORGANISM.run(ta.value);
      const lines = [];
      lines.push("=== v3.8.0 demo (in-browser, v0.1) ===");
      lines.push("problema: " + ta.value);
      lines.push("");
      r.steps.forEach((s) => lines.push(s));
      lines.push("");
      lines.push("final:");
      lines.push("  pick = " + r.final.pick.id + " · ρ = " + global.OSX_ORGANISM.rho(r.final.pick).toFixed(4));
      lines.push("  PBR = " + r.final.pbr);
      lines.push("  Ω   = " + r.final.omega.toFixed(4));
      out.textContent = lines.join("\n");
      document.getElementById("osx-omega-value").textContent = r.final.omega.toFixed(2);
    });
    omegaBtn.addEventListener("click", () => {
      const o = global.OSX_ORGANISM.recalcOmega(21.91);
      out.textContent = "Ω recalculado = " + o.toFixed(4) + " (canonical 5-dim, all in [0,1])";
      document.getElementById("osx-omega-value").textContent = o.toFixed(2);
    });
    mmnbBtn.addEventListener("click", () => {
      const m = global.OSX_ORGANISM.newMMNB();
      out.textContent = JSON.stringify(m, null, 2);
    });
  }

  // ---------------------- Top bar / dock bind ----------------------
  function bindNav() {
    document.querySelectorAll("[data-view]").forEach((el) => {
      el.addEventListener("click", (e) => {
        const v = el.dataset.view;
        if (v) OSX.setView(v);
      });
    });
    // zoom controls
    document.querySelectorAll("[data-zoom]").forEach((btn) => {
      btn.addEventListener("click", () => {
        // naive: redraw the constellation at the new zoom
        renderConstellation();
        const lvl = document.getElementById("osx-zoom-level");
        if (lvl) lvl.textContent = (1.0).toFixed(1) + "×";
      });
    });
    // human node click
    document.getElementById("osx-human-node").addEventListener("click", () => {
      alert("Human Node · Mateus\n\nRepresentação visual da identidade declarada.\nAvatar ≠ autenticação. Avatar ≠ assinatura.\n\nAutoridade operacional: sessões e chaves continuam separadas.");
    });
  }

  // ---------------------- Init ----------------------
  function init() {
    bindNav();
    renderConstellation();
    renderAtlas();
    renderRegistry();
    renderNotebookList("");
    openNotebook(currentNb.id);
    bindCassandra();
    bindFigureLab();
    bindOrganism();
    global.OSX_CANVAS.init();
    // initial omega display
    document.getElementById("osx-omega-value").textContent = global.OSX.omegaScore(0.92, 21.91, 4.0, 0.78, 0.85).toFixed(2);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})(window);
