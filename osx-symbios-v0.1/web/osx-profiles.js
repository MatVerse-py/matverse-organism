/* =================================================================
   osx-profiles.js  ·  Catálogo de Perfis (Page 2 of 5)
   =================================================================
   Identity + Capacity registry for the whole MatVerse.

   Separations (mandatory):
     User ≠ Agent
     Agent ≠ Skill
     Skill ≠ Capability
     Capability ≠ Authorization
     Profile ≠ Active session

   Cardinal rule: "Catálogo de Perfis não deve ser limitado aos
   agentes Cassandra. Ele deve ser o Registry humano–agente–
   skill–capability de todo o MatVerse."

   Entities:
     UserProfile, AgentProfile, Role, Permission, AgentAssignment,
     AgentSkillBinding, CapabilityGrant, UserSession,
     AgentConversation, AgentMessage, AuthorizationRequest,
     AgentExecution, AgentAuditEvent
   ================================================================= */
(function (global) {
  "use strict";

  // ---- 5 agent catalogs (per the corpus) ----
  const CATALOGS = {
    CASSANDRA: {
      name: "Cassandra",
      role: "cognitive interpretation + L3 learning",
      skills: [
        { id: "CASS-INTERPRETER",     name: "Interpreter",     desc: "interpreta intenção e classifica epistemicamente" },
        { id: "CASS-DEEP-EXPLAIN",    name: "Deep Explain",    desc: "explica o organismo em profundidade" },
        { id: "CASS-CORPUS-CROSSING", name: "Corpus Crossing", desc: "atravessa o corpus e conecta fontes" },
        { id: "CASS-RESEARCH",        name: "Research",        desc: "orquestra research com grounding" },
        { id: "CASS-RED-TEAM",        name: "Red Team",        desc: "stress-testa a posição constitucional" },
        { id: "CASS-RECONCILIATION",  name: "Reconciliation",  desc: "reconcilia fontes divergentes" },
        { id: "CASS-COMPOSER",        name: "Composer",        desc: "compõe resposta estruturada" },
      ],
    },
    ATLAS: {
      name: "Atlas",
      role: "live cartographic projection",
      skills: [
        { id: "ATL-SCOPE",      name: "Scope Agent",     desc: "define o escopo da busca" },
        { id: "ATL-SOURCE",     name: "Source Agent",    desc: "seleciona fontes executáveis" },
        { id: "ATL-CLAIM",      name: "Claim Agent",     desc: "extrai claims verificáveis" },
        { id: "ATL-EVIDENCE",   name: "Evidence Agent",  desc: "anota evidências" },
        { id: "ATL-CONTRADICT", name: "Contradiction",   desc: "detecta contradições" },
        { id: "ATL-GAP",        name: "Gap Agent",       desc: "identifica lacunas" },
        { id: "ATL-TIMELINE",   name: "Timeline Agent",  desc: "ordena eventos" },
        { id: "ATL-DOSSIER",    name: "Dossier Agent",   desc: "compila dossiê verificável" },
      ],
    },
    URANO: {
      name: "URANO",
      role: "experimental laboratory",
      skills: [
        { id: "URN-HYP",     name: "Hypothesis Agent",     desc: "gera hipóteses falsificáveis" },
        { id: "URN-COMPILE", name: "Experiment Compiler",  desc: "compila o experimento" },
        { id: "URN-SIM",     name: "Simulation Agent",     desc: "executa simulação" },
        { id: "URN-BENCH",   name: "Benchmark Agent",      desc: "mede contra baseline" },
        { id: "URN-FALSIFY", name: "Falsification Agent",  desc: "tenta falsificar" },
        { id: "URN-PACK",    name: "Evidence Pack Agent",  desc: "empacota evidência" },
      ],
    },
    SYMBIOS: {
      name: "SymbiOS",
      role: "network notebook + node operator",
      skills: [
        { id: "SYM-ENGINEER", name: "Engineer",     desc: "engenharia do notebook" },
        { id: "SYM-CODE",     name: "Code Agent",   desc: "gera código do nó" },
        { id: "SYM-TEST",     name: "Test Agent",   desc: "testa o nó" },
        { id: "SYM-BUILD",    name: "Build Agent",  desc: "constrói o nó" },
        { id: "SYM-DEPLOY",   name: "Deploy Agent", desc: "publica o nó (esc/hold por padrão)" },
        { id: "SYM-ROLLBACK", name: "Rollback",     desc: "reverte o nó" },
        { id: "SYM-OPERATOR", name: "Node Operator", desc: "opera o nó em runtime" },
      ],
    },
    EVIDENCEOS: {
      name: "EvidenceOS",
      role: "proof + continuity",
      skills: [
        { id: "EVD-POLICY",   name: "Policy Evaluator",  desc: "avalia política" },
        { id: "EVD-RECEIPT",  name: "Receipt Generator", desc: "gera receipt" },
        { id: "EVD-LEDGER",   name: "Ledger Verifier",   desc: "verifica ledger" },
        { id: "EVD-REPLAY",   name: "Replay Agent",      desc: "re-executa receipt" },
        { id: "EVD-AUDIT",    name: "Audit Agent",       desc: "audita trilha" },
      ],
    },
  };

  // ---- AXIS-8 (per the corpus) — appear as review skills, not users ----
  const AXIS_8 = [
    { id: "AX-TRUTHMODE", name: "TRUTHMODE", desc: "modo verdade: sem coerência narrativa sem evidência" },
    { id: "AX-REDTEAM",   name: "REDTEAM",   desc: "stress-test constitucional" },
    { id: "AX-UNLEARN",   name: "UNLEARN",   desc: "limpa o que o sistema aprendeu errado" },
    { id: "AX-8020",      name: "80/20",     desc: "foco no que produz 80% do resultado" },
    { id: "AX-HORMOZI",   name: "HORMOZI",   desc: "frame de grandezas e alavancas" },
    { id: "AX-FUTUREYOU", name: "FUTUREYOU", desc: "projeta intenção para o futuro" },
    { id: "AX-HUMAN",     name: "/human",    desc: "ancoragem na voz humana" },
    { id: "AX-HAXIS",     name: "H-Axis",    desc: "eixo horizontal: do informacional ao físico" },
  ];

  // ---- Roles (RBAC) ----
  const ROLES = [
    { id: "ROLE-OPERATOR",      name: "Operator",      permissions: ["INTENT.CREATE", "INTENT.ESCALATE", "PUBLISH.SIGN", "EVIDENCE.WITNESS"] },
    { id: "ROLE-AUDITOR",       name: "Auditor",       permissions: ["EVIDENCE.VERIFY", "LEDGER.READ", "REPLAY.EXECUTE"] },
    { id: "ROLE-RESEARCHER",    name: "Researcher",    permissions: ["INTENT.CREATE", "NOTEBOOK.READ", "NOTEBOOK.WRITE"] },
    { id: "ROLE-AGENT-DEPLOY",  name: "Agent Deployer", permissions: ["AGENT.DEPLOY", "GRANT.MINT", "AGENT.REVOKE"] },
    { id: "ROLE-OBSERVER",      name: "Observer",      permissions: ["NOTEBOOK.READ", "EVIDENCE.READ"] },
  ];

  // ---- Permissions catalog ----
  const PERMISSIONS = [
    { id: "INTENT.CREATE",        scope: "intent" },
    { id: "INTENT.ESCALATE",      scope: "intent" },
    { id: "PUBLISH.SIGN",         scope: "publication" },
    { id: "EVIDENCE.WITNESS",     scope: "evidence" },
    { id: "EVIDENCE.VERIFY",      scope: "evidence" },
    { id: "EVIDENCE.READ",        scope: "evidence" },
    { id: "LEDGER.READ",          scope: "ledger" },
    { id: "REPLAY.EXECUTE",       scope: "evidence" },
    { id: "NOTEBOOK.READ",        scope: "notebook" },
    { id: "NOTEBOOK.WRITE",       scope: "notebook" },
    { id: "AGENT.DEPLOY",         scope: "agent" },
    { id: "AGENT.REVOKE",         scope: "agent" },
    { id: "GRANT.MINT",           scope: "agent" },
  ];

  // ---- Users ----
  const USERS = [
    { id: "USR-MATEUS",   human_node_id: "HUMAN-MATEUS-001", display_name: "Mateus",  roles: ["ROLE-OPERATOR", "ROLE-AUDITOR"] },
    { id: "USR-CASSANDRA", human_node_id: "HUMAN-CASSANDRA", display_name: "Cassandra Human", roles: ["ROLE-OBSERVER"] },
  ];

  // ---- Agents (the 5 families) ----
  const AGENTS = [
    { id: "AGT-CASS-INTERPRETER",  profile_id: "CASS", status: "ACTIVE",  catalog: "CASSANDRA", skill: "CASS-INTERPRETER" },
    { id: "AGT-CASS-DEEP-EXPLAIN", profile_id: "CASS", status: "ACTIVE",  catalog: "CASSANDRA", skill: "CASS-DEEP-EXPLAIN" },
    { id: "AGT-ATL-SCOPE",         profile_id: "ATL",  status: "ACTIVE",  catalog: "ATLAS",     skill: "ATL-SCOPE" },
    { id: "AGT-ATL-SOURCE",        profile_id: "ATL",  status: "ACTIVE",  catalog: "ATLAS",     skill: "ATL-SOURCE" },
    { id: "AGT-ATL-CLAIM",         profile_id: "ATL",  status: "ACTIVE",  catalog: "ATLAS",     skill: "ATL-CLAIM" },
    { id: "AGT-URN-HYP",           profile_id: "URN",  status: "PROTOTYPE", catalog: "URANO", skill: "URN-HYP" },
    { id: "AGT-URN-COMPILE",       profile_id: "URN",  status: "PROTOTYPE", catalog: "URANO", skill: "URN-COMPILE" },
    { id: "AGT-URN-SIM",           profile_id: "URN",  status: "HOLD",     catalog: "URANO", skill: "URN-SIM" },
    { id: "AGT-SYM-ENGINEER",      profile_id: "SYM",  status: "ACTIVE",  catalog: "SYMBIOS",   skill: "SYM-ENGINEER" },
    { id: "AGT-SYM-DEPLOY",        profile_id: "SYM",  status: "HOLD",     catalog: "SYMBIOS",   skill: "SYM-DEPLOY" },
    { id: "AGT-EVD-POLICY",        profile_id: "EVD",  status: "ACTIVE",  catalog: "EVIDENCEOS", skill: "EVD-POLICY" },
    { id: "AGT-EVD-RECEIPT",       profile_id: "EVD",  status: "ACTIVE",  catalog: "EVIDENCEOS", skill: "EVD-RECEIPT" },
    { id: "AGT-EVD-LEDGER",        profile_id: "EVD",  status: "ACTIVE",  catalog: "EVIDENCEOS", skill: "EVD-LEDGER" },
    { id: "AGT-EVD-REPLAY",        profile_id: "EVD",  status: "ACTIVE",  catalog: "EVIDENCEOS", skill: "EVD-REPLAY" },
  ];

  // ---- Agent Assignments (User → Agent) ----
  const ASSIGNMENTS = [
    { id: "ASN-001", user_id: "USR-MATEUS", agent_id: "AGT-CASS-INTERPRETER", role_id: "ROLE-OPERATOR" },
    { id: "ASN-002", user_id: "USR-MATEUS", agent_id: "AGT-ATL-SCOPE",        role_id: "ROLE-OPERATOR" },
    { id: "ASN-003", user_id: "USR-MATEUS", agent_id: "AGT-EVD-LEDGER",       role_id: "ROLE-AUDITOR" },
    { id: "ASN-004", user_id: "USR-MATEUS", agent_id: "AGT-SYM-DEPLOY",       role_id: "ROLE-AGENT-DEPLOY" },
  ];

  // ---- Capability Grants (time-limited) ----
  const GRANTS = [
    { id: "GRT-001", agent_id: "AGT-CASS-INTERPRETER", capability_id: "INTENT.INTERPRET",   issued_at: 0, ttl_seconds: 600, scope: {} },
    { id: "GRT-002", agent_id: "AGT-ATL-SCOPE",        capability_id: "NOTEBOOK.READ",      issued_at: 0, ttl_seconds: 600, scope: { notebook_id: "*" } },
    { id: "GRT-003", agent_id: "AGT-EVD-LEDGER",       capability_id: "LEDGER.READ",        issued_at: 0, ttl_seconds: 600, scope: {} },
    { id: "GRT-004", agent_id: "AGT-SYM-DEPLOY",       capability_id: "NOTEBOOK.DEPLOY",    issued_at: 0, ttl_seconds: 600, scope: { requires_operator: true } },
  ];

  // ---- User Sessions (active ones) ----
  const SESSIONS = [
    { id: "SES-001", user_id: "USR-MATEUS", issued_at: 0, expires_at: 3600, mfa: true,  ip_hash: "h-ip-1" },
    { id: "SES-002", user_id: "USR-CASSANDRA", issued_at: 0, expires_at: 3600, mfa: false, ip_hash: "h-ip-2" },
  ];

  // ---- Agent Conversations (Cassandra running) ----
  const CONVERSATIONS = [
    { id: "CONV-001", user_id: "USR-MATEUS", agent_id: "AGT-CASS-INTERPRETER", started_at: 0, messages: 3, state: "ACTIVE" },
    { id: "CONV-002", user_id: "USR-MATEUS", agent_id: "AGT-CASS-DEEP-EXPLAIN", started_at: 0, messages: 1, state: "ACTIVE" },
  ];

  // ---- Authorization Requests (operator pre-flight) ----
  const AUTHZ_REQUESTS = [
    { id: "AZR-001", user_id: "USR-MATEUS", agent_id: "AGT-SYM-DEPLOY", capability_id: "NOTEBOOK.DEPLOY", decision: "PENDING",  decided_at: null },
    { id: "AZR-002", user_id: "USR-MATEUS", agent_id: "AGT-URN-SIM",   capability_id: "EXPERIMENT.RUN",  decision: "APPROVED", decided_at: 100 },
    { id: "AZR-003", user_id: "USR-MATEUS", agent_id: "AGT-SYM-DEPLOY", capability_id: "NOTEBOOK.DEPLOY", decision: "DENIED",   decided_at: 200 },
  ];

  // ---- Audit Events (append-only log) ----
  const AUDIT_EVENTS = [
    { id: "AUD-001", at: 0, actor: "USR-MATEUS", action: "INTENT.CREATE",    target: "INT-0001" },
    { id: "AUD-002", at: 1, actor: "USR-MATEUS", action: "INTENT.ESCALATE",  target: "INT-0003" },
    { id: "AUD-003", at: 2, actor: "USR-MATEUS", action: "AGENT.DEPLOY.DENY", target: "AZR-003" },
  ];

  // ---- helpers ----
  function findUser(id) { return USERS.filter((u) => u.id === id)[0] || null; }
  function findAgent(id) { return AGENTS.filter((a) => a.id === id)[0] || null; }
  function findRole(id) { return ROLES.filter((r) => r.id === id)[0] || null; }
  function findPermission(id) { return PERMISSIONS.filter((p) => p.id === id)[0] || null; }
  function agentsByCatalog(catalog_id) { return AGENTS.filter((a) => a.catalog === catalog_id); }
  function grantsForAgent(agent_id) { return GRANTS.filter((g) => g.agent_id === agent_id); }
  function isGrantValid(g, now) {
    if (now === undefined) now = 0;
    return (now - g.issued_at) < g.ttl_seconds;
  }

  // ---- summary across the catalog ----
  function summary() {
    const by_status = { ACTIVE: 0, HOLD: 0, PROTOTYPE: 0, REVOKED: 0 };
    AGENTS.forEach((a) => { by_status[a.status] = (by_status[a.status] || 0) + 1; });
    return {
      catalogs: Object.keys(CATALOGS).length,
      axis_8: AXIS_8.length,
      roles: ROLES.length,
      permissions: PERMISSIONS.length,
      users: USERS.length,
      agents: AGENTS.length,
      grants: GRANTS.length,
      sessions: SESSIONS.length,
      conversations: CONVERSATIONS.length,
      authz_requests: AUTHZ_REQUESTS.length,
      audit_events: AUDIT_EVENTS.length,
      by_status: by_status,
    };
  }

  // ---- EXPORT ----
  global.OSX_PROFILES = {
    CATALOGS: CATALOGS,
    AXIS_8: AXIS_8,
    ROLES: ROLES,
    PERMISSIONS: PERMISSIONS,
    USERS: USERS,
    AGENTS: AGENTS,
    ASSIGNMENTS: ASSIGNMENTS,
    GRANTS: GRANTS,
    SESSIONS: SESSIONS,
    CONVERSATIONS: CONVERSATIONS,
    AUTHZ_REQUESTS: AUTHZ_REQUESTS,
    AUDIT_EVENTS: AUDIT_EVENTS,
    findUser: findUser,
    findAgent: findAgent,
    findRole: findRole,
    findPermission: findPermission,
    agentsByCatalog: agentsByCatalog,
    grantsForAgent: grantsForAgent,
    isGrantValid: isGrantValid,
    summary: summary,
  };
})(typeof window !== "undefined" ? window : global);
