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

  // ---------------------- SymbiOS module · 5 new pages ----------------------

  function renderIntent() {
    const I = global.OSX_INTENT;
    if (!I) return;
    // FSM (12 states + transitions)
    const fsmLines = ["12 estados canônicos:"];
    I.STATES.forEach((s) => {
      const t = I.TRANSITIONS[s] || [];
      fsmLines.push("  " + s + " → [" + t.join(", ") + "]");
    });
    document.getElementById("osx-intent-fsm").textContent = fsmLines.join("\n");

    // Seed table
    const tbody = document.getElementById("osx-intent-tbody");
    tbody.innerHTML = "";
    I.SAMPLE.forEach((it) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + it.intent_id + "</td>"
        + "<td>" + it.intent_class + "</td>"
        + "<td>" + (it.statement.length > 60 ? it.statement.slice(0, 60) + "…" : it.statement) + "</td>"
        + "<td>" + it.risk + "</td>"
        + "<td>" + (it.external_effect ? "yes" : "no") + "</td>"
        + "<td><b>" + it.state + "</b></td>";
      tbody.appendChild(tr);
    });

    // Summary
    const sum = I.summary(I.SAMPLE);
    const sumLines = [];
    sumLines.push("total:        " + sum.total);
    sumLines.push("active:       " + sum.active);
    sumLines.push("blocked:      " + sum.blocked);
    sumLines.push("terminal:     " + sum.terminal);
    sumLines.push("");
    sumLines.push("by_state:");
    Object.keys(sum.by_state).forEach((k) => sumLines.push("  " + k.padEnd(26) + sum.by_state[k]));
    document.getElementById("osx-intent-summary").textContent = sumLines.join("\n");

    // New intent: route
    document.getElementById("osx-intent-route").addEventListener("click", () => {
      const stmt = document.getElementById("osx-intent-stmt").value.trim() || "(vazio)";
      const cls = document.getElementById("osx-intent-class").value;
      const risk = document.getElementById("osx-intent-risk").value;
      const ext = document.getElementById("osx-intent-external").checked;
      const it = I.newIntent({
        statement: stmt, intent_class: cls, risk: risk, external_effect: ext,
      });
      // walk: RECEIVED → CLASSIFIED → DECOMPOSED → ROUTED
      I.transition(it, "CLASSIFIED");
      const dec = I.decompose(it);
      I.transition(it, "DECOMPOSED");
      I.transition(it, dec.routing === "WAITING_AUTHORIZATION" ? "WAITING_AUTHORIZATION" : "ROUTED");
      const out = ["Intent criada: " + it.intent_id];
      out.push("  classe:     " + it.intent_class);
      out.push("  risk:       " + it.risk);
      out.push("  external:   " + it.external_effect);
      out.push("  state:      " + it.state);
      out.push("  routing:    " + dec.routing);
      out.push("  reason:     " + dec.reason);
      out.push("  subtasks:");
      dec.subtasks.forEach((s) => out.push("    - " + s.kind + " on " + s.target));
      document.getElementById("osx-intent-new-out").textContent = out.join("\n");
    });
  }

  function renderProfiles() {
    const P = global.OSX_PROFILES;
    if (!P) return;
    // Catalogs
    const cul = document.getElementById("osx-pr-catalogs");
    cul.innerHTML = "";
    Object.keys(P.CATALOGS).forEach((k) => {
      const c = P.CATALOGS[k];
      const li = document.createElement("li");
      li.innerHTML = "<b>" + c.name + "</b> — " + c.role + " <i>(" + c.skills.length + " skills)</i>";
      cul.appendChild(li);
    });
    // AXIS-8
    const ax = document.getElementById("osx-pr-axis8");
    ax.innerHTML = "";
    P.AXIS_8.forEach((s) => {
      const li = document.createElement("li");
      li.innerHTML = "<code>" + s.id + "</code> " + s.name + " — " + s.desc;
      ax.appendChild(li);
    });
    // RBAC
    const rt = document.getElementById("osx-pr-rbac-tbody");
    rt.innerHTML = "";
    P.ROLES.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + r.id + "</td><td>" + r.permissions.join(", ") + "</td>";
      rt.appendChild(tr);
    });
    // Agents by status
    const al = document.getElementById("osx-pr-agents");
    al.innerHTML = "";
    const sum = P.summary();
    Object.keys(sum.by_status).forEach((s) => {
      const li = document.createElement("li");
      li.innerHTML = "<b>" + s + "</b>: " + sum.by_status[s] + " agents";
      al.appendChild(li);
    });
    P.AGENTS.forEach((a) => {
      const li = document.createElement("li");
      li.innerHTML = a.id + " <i>(" + a.catalog + " / " + a.skill + ")</i>";
      al.appendChild(li);
    });
    // Grants
    const gl = document.getElementById("osx-pr-grants");
    gl.innerHTML = "";
    P.GRANTS.forEach((g) => {
      const li = document.createElement("li");
      li.innerHTML = "<code>" + g.id + "</code> " + g.agent_id + " → " + g.capability_id
        + " (TTL " + g.ttl_seconds + "s, " + (P.isGrantValid(g) ? "valid" : "EXPIRED") + ")";
      gl.appendChild(li);
    });
    // Audit
    const au = document.getElementById("osx-pr-audit");
    au.innerHTML = "";
    P.AUDIT_EVENTS.forEach((e) => {
      const li = document.createElement("li");
      li.innerHTML = "[" + e.at + "] <b>" + e.actor + "</b> " + e.action + " → " + e.target;
      au.appendChild(li);
    });
  }

  function renderNodes() {
    const N = global.OSX_NODES;
    if (!N) return;
    // Types
    const tu = document.getElementById("osx-nd-types");
    tu.innerHTML = "";
    N.NODE_TYPES.forEach((t) => {
      const li = document.createElement("li");
      li.innerHTML = "<b>" + t + "</b> <i>(" + N.LENS_OF[t] + ")</i>";
      tu.appendChild(li);
    });
    // Relations
    const ru = document.getElementById("osx-nd-rels");
    ru.innerHTML = "";
    N.RELATION_TYPES.forEach((r) => {
      const li = document.createElement("li");
      li.innerHTML = r;
      ru.appendChild(li);
    });
    // Lenses
    const lu = document.getElementById("osx-nd-lenses");
    lu.innerHTML = "";
    const sum = N.summary();
    Object.keys(sum.by_lens).forEach((k) => {
      const li = document.createElement("li");
      li.innerHTML = "<b>" + k + "</b>: " + sum.by_lens[k] + " nodes";
      lu.appendChild(li);
    });
    // Summary
    const sumLines = ["total_nodes: " + sum.total_nodes, "total_edges: " + sum.total_edges, ""];
    sumLines.push("by_type:");
    Object.keys(sum.by_type).forEach((k) => sumLines.push("  " + k.padEnd(20) + sum.by_type[k]));
    sumLines.push("");
    sumLines.push("edges_by_type:");
    Object.keys(sum.edges_by_type).forEach((k) => sumLines.push("  " + k.padEnd(20) + sum.edges_by_type[k]));
    document.getElementById("osx-nd-summary").textContent = sumLines.join("\n");
    // Levels
    document.querySelectorAll(".osx-nd-level").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".osx-nd-level").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const level = btn.dataset.level;
        const fn = N[level.toUpperCase()];
        const nodes = fn();
        const lines = [level.toUpperCase() + " navigation · " + nodes.length + " nodes", ""];
        nodes.forEach((n) => lines.push("  " + n.node_id + "  " + n.type + "  " + n.label));
        document.getElementById("osx-nd-level-out").textContent = lines.join("\n");
      });
    });
    // SVG layout (deterministic: ring by lens)
    drawNodesGraph();
  }

  function drawNodesGraph() {
    const N = global.OSX_NODES;
    if (!N) return;
    const svg = document.getElementById("osx-nd-svg");
    if (!svg) return;
    // simple force-like layout: 3 concentric rings (informational / digital / physical)
    const cx = 400, cy = 250;
    const radii = { informational: 60, digital: 130, physical: 200 };
    const positions = {};
    const nodesByLens = { informational: [], digital: [], physical: [] };
    N.NODES.forEach((n) => nodesByLens[n.lens].push(n));
    Object.keys(nodesByLens).forEach((lens) => {
      const list = nodesByLens[lens];
      const r = radii[lens];
      list.forEach((n, i) => {
        const angle = (i / list.length) * 2 * Math.PI;
        positions[n.node_id] = {
          x: cx + r * Math.cos(angle),
          y: cy + r * Math.sin(angle),
          type: n.type, lens: n.lens, label: n.label,
        };
      });
    });
    // render
    let html = "";
    // edges first
    N.EDGES.forEach((e) => {
      const a = positions[e.source_id], b = positions[e.target_id];
      if (!a || !b) return;
      const color = e.type === "CONTRADICTS" ? "#c44b4b" : (e.type === "SUPERSEDES" ? "#5fd2a4" : "#7a8290");
      html += '<line x1="' + a.x.toFixed(1) + '" y1="' + a.y.toFixed(1)
        + '" x2="' + b.x.toFixed(1) + '" y2="' + b.y.toFixed(1)
        + '" stroke="' + color + '" stroke-width="0.6" opacity="0.55" />';
    });
    // nodes
    Object.keys(positions).forEach((id) => {
      const p = positions[id];
      const fill = p.lens === "informational" ? "#5fd2a4" : (p.lens === "digital" ? "#9b87f5" : "#d6c25a");
      html += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="3.5" fill="' + fill + '" stroke="#0e0f12" stroke-width="0.6" />';
    });
    svg.innerHTML = html;
  }

  function renderEvidence() {
    const E = global.OSX_EVIDENCE;
    if (!E) return;
    // 10 states
    const ul = document.getElementById("osx-ev-states");
    ul.innerHTML = "";
    E.STATES.forEach((s) => {
      const li = document.createElement("li");
      li.innerHTML = "<b>" + s + "</b>";
      ul.appendChild(li);
    });
    // Decisions
    const dt = document.getElementById("osx-ev-decisions-tbody");
    dt.innerHTML = "";
    E.SAMPLE_DECISIONS.forEach((d) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + d.decision_id + "</td><td>" + d.policy_id + "</td><td>" + d.agent_id + "</td><td>" + d.capability_id + "</td><td><b>" + d.status + "</b></td>";
      dt.appendChild(tr);
    });
    // Receipts
    const rt = document.getElementById("osx-ev-receipts-tbody");
    rt.innerHTML = "";
    E.SAMPLE_RECEIPTS.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + r.receipt_id + "</td><td>" + r.hash_in + "</td><td>" + (r.hash_out || "—") + "</td><td>" + (r.prev_receipt || "—") + "</td><td>" + r.replay_status + "</td><td>" + r.witness_status + "</td>";
      rt.appendChild(tr);
    });
    // Ledger
    const lLines = ["ledger_id: " + E.SAMPLE_LEDGER.ledger_id, "entries: " + E.SAMPLE_LEDGER.entries.length, "root_hash: " + E.SAMPLE_LEDGER.root_hash, "valid: " + E.SAMPLE_LEDGER.verify(), ""];
    E.SAMPLE_LEDGER.entries.forEach((e) => {
      lLines.push("  " + e.receipt_id + "  hash=" + e.hash + "  prev=" + e.prev_hash);
    });
    document.getElementById("osx-ev-ledger").textContent = lLines.join("\n");
    // Replays
    const rl = document.getElementById("osx-ev-replays");
    rl.innerHTML = "";
    E.SAMPLE_REPLAYS.forEach((r) => {
      const li = document.createElement("li");
      li.innerHTML = "<b>" + r.replay_id + "</b> on " + r.receipt_id + " → " + r.status + " (" + r.compared_with_original + ", witness=" + r.witness_status + ")";
      rl.appendChild(li);
    });
    // Verify chain
    const vLines = [];
    E.SAMPLE_RECEIPTS.forEach((r) => {
      const d = E.SAMPLE_DECISIONS.filter((x) => x.decision_id === r.decision_id)[0];
      const rpls = E.SAMPLE_REPLAYS.filter((x) => x.receipt_id === r.receipt_id);
      const v = E.verifyChain(d, r, E.SAMPLE_LEDGER, rpls);
      vLines.push(r.receipt_id + ": " + v.verdict);
    });
    document.getElementById("osx-ev-verify").textContent = vLines.join("\n");
  }

  function renderSGI() {
    const S = global.OSX_SGI;
    if (!S) return;
    // Rules
    const ul = document.getElementById("osx-sgi-rules");
    ul.innerHTML = "";
    Object.keys(S.EXPORT_RULES).forEach((k) => {
      const r = S.EXPORT_RULES[k];
      const li = document.createElement("li");
      li.innerHTML = "<b>" + k + "</b> — can_publish=" + r.can_publish + ", must_label=" + r.must_label + ", requires_attestation=" + r.requires_attestation;
      ul.appendChild(li);
    });
    // Summary
    const sum = S.summary();
    const sLines = ["total:           " + sum.total, "publishable:     " + sum.publishable, "blocked:         " + sum.blocked, "formats:         " + sum.formats, "", "by_epistemic:"];
    Object.keys(sum.by_epistemic).forEach((k) => sLines.push("  " + k.padEnd(16) + sum.by_epistemic[k]));
    document.getElementById("osx-sgi-summary").textContent = sLines.join("\n");
    // Table
    const tb = document.getElementById("osx-sgi-tbody");
    tb.innerHTML = "";
    S.SAMPLE_METRICS.forEach((m) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + m.metric_id + "</td>"
        + "<td>" + m.name + "</td>"
        + "<td>" + m.epistemic + "</td>"
        + "<td>" + (m.value === null ? "n/a" : m.value) + "</td>"
        + "<td>" + m.unit + "</td>"
        + "<td>" + (m.source.length > 40 ? m.source.slice(0, 40) + "…" : m.source) + "</td>"
        + '<td class="' + (S.canPublish(m) ? "can-yes" : "can-no") + '">' + (S.canPublish(m) ? "YES" : "NO") + "</td>"
        + '<td class="' + (S.mustLabel(m) ? "label-yes" : "label-no") + '">' + (S.mustLabel(m) ? "YES" : "no") + "</td>";
      tb.appendChild(tr);
    });
    // Export button
    document.getElementById("osx-sgi-export").addEventListener("click", () => {
      const fmt = document.getElementById("osx-sgi-fmt").value;
      let out = "";
      if (fmt === "JSON")        out = S.toJSON();
      else if (fmt === "CSV")    out = S.toCSV();
      else if (fmt === "MARKDOWN") out = S.toMarkdown(S.publishable());
      else if (fmt === "OPENLINEAGE") out = S.toOpenLineageEvent();
      else if (fmt === "INTOTO") out = S.toInTotoAttestation();
      document.getElementById("osx-sgi-out").textContent = out;
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
    // SymbiOS module · 5 new pages
    renderIntent();
    renderProfiles();
    renderNodes();
    renderEvidence();
    renderSGI();
    // initial omega display
    document.getElementById("osx-omega-value").textContent = global.OSX.omegaScore(0.92, 21.91, 4.0, 0.78, 0.85).toFixed(2);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})(window);
