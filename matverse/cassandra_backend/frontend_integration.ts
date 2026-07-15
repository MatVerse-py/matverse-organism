/**
 * frontend_integration.ts
 * =======================
 *
 * Drop-in TypeScript snippet for the Base44 "Cassandra Cube" app
 * (https://app.base44.com/apps/6a3f8b077390fd927d6fd4bf/editor) to
 * call the Cassandra backend.
 *
 * Place this file in `src/lib/cassandra.ts` in the Base44 app, then
 * import and use `cassandra.chat(message)` from the Copilot page.
 *
 * The base44 SDK should NOT be used for the chat call — only for
 * data entities (User, etc.). The chat goes through THIS backend
 * because:
 *   1. It enforces the 5 hard limits server-side (constitutional)
 *   2. It uses the v3.8.2 session/capability token model (secure)
 *   3. It never sends the api_key on the chat path (no leakage)
 *   4. It is self-hostable (no Base44 lock-in for the chat)
 */

// ---- Configuration ----

const CASSANDRA_BACKEND_URL =
  (import.meta as any).env?.VITE_CASSANDRA_BACKEND_URL ||
  "http://127.0.0.1:8787";

const CASSANDRA_API_KEY =
  (import.meta as any).env?.VITE_CASSANDRA_API_KEY || "";

// IMPORTANT: in production, the api_key is loaded from a build-time
// env var, NEVER from user input or localStorage. In Base44, set it
// in the "Secrets" section of the app config (not in client code).

// ---- Types ----

export type GateStatus = "PASS" | "HOLD" | "ESCALATE" | "DENY";
export type Epistemic =
  | "NULL" | "OBS" | "INF" | "HYP" | "EVD" | "ADM" | "CON" | "ESC";

export interface ChatResponse {
  run_id: string;
  response: string;
  gate_status: GateStatus;
  epistemic: Epistemic;
  triggered_limits: number[];
  needs_operator: boolean;
  route_used: "ZERO" | "TINY" | "BURST";
  model_used: string;
  agent_id: string;
  skill_name: string;
  user_id: string;
  context: Record<string, unknown>;
  issued_at: number;
  policy_version: string;
  constitutional_position: string;
}

// ---- Token cache (in-memory only, never persisted) ----

let sessionToken: string | null = null;
let sessionExpiresAt = 0;
let capabilityToken: string | null = null;
let capabilityExpiresAt = 0;

// ---- Internal: refresh session token if needed ----

async function ensureSession(): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (sessionToken && now < sessionExpiresAt - 60) {
    return sessionToken;
  }

  const resp = await fetch(`${CASSANDRA_BACKEND_URL}/auth/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: CASSANDRA_API_KEY, ttl_seconds: 3600 }),
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`auth/session failed: ${err.error || resp.statusText}`);
  }

  const data = await resp.json();
  sessionToken = data.session_token;
  sessionExpiresAt = now + data.expires_in;
  // CRITICAL: drop the api_key from any closure or local variable
  // immediately. The backend also drops it from its memory.
  return sessionToken;
}

// ---- Internal: refresh capability token if needed ----

async function ensureCapability(
  agentId: string,
  skillName: string,
  allowBurst = false,
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (capabilityToken && now < capabilityExpiresAt - 60) {
    return capabilityToken;
  }

  const session = await ensureSession();
  const resp = await fetch(`${CASSANDRA_BACKEND_URL}/auth/capability`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session}`,
    },
    body: JSON.stringify({
      agent_id: agentId,
      skill_name: skillName,
      ttl_seconds: 600,
      scope: { allow_burst: allowBurst },
    }),
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`auth/capability failed: ${err.error || resp.statusText}`);
  }

  const data = await resp.json();
  capabilityToken = data.capability_token;
  capabilityExpiresAt = now + data.expires_in;
  return capabilityToken;
}

// ---- Public API: chat with Cassandra ----

export async function chat(
  message: string,
  context: Record<string, unknown> = {},
  options: { agentId?: string; skillName?: string; preferBurst?: boolean } = {},
): Promise<ChatResponse> {
  const {
    agentId = "cassandra",
    skillName = "interpret",
    preferBurst = false,
  } = options;

  const cap = await ensureCapability(agentId, skillName, preferBurst);
  const resp = await fetch(`${CASSANDRA_BACKEND_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${cap}`,
    },
    body: JSON.stringify({ message, context, prefer_burst: preferBurst }),
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`chat failed: ${err.error || resp.statusText}`);
  }

  return resp.json();
}

// ---- Public API: get the system prompt (for transparency) ----

export async function getSystemPrompt(): Promise<string> {
  const resp = await fetch(`${CASSANDRA_BACKEND_URL}/system-prompt`);
  if (!resp.ok) throw new Error("system-prompt fetch failed");
  const data = await resp.json();
  return data.system_prompt;
}

// ---- Public API: health check ----

export async function health(): Promise<{ status: string; version: string }> {
  const resp = await fetch(`${CASSANDRA_BACKEND_URL}/health`);
  if (!resp.ok) throw new Error("health check failed");
  return resp.json();
}

// ---- Constitutional guard: NEVER let an ESCALATE / DENY trigger a Base44 action ----

/**
 * Call this BEFORE any Base44 mutation (createEntity, updateEntity,
 * invokeLLM, etc.) to verify that the gate is PASS or HOLD. If the
 * gate is ESCALATE or DENY, the action MUST be blocked.
 */
export function assertConstitutionalGate(
  response: ChatResponse,
  action: string,
): void {
  if (response.gate_status === "ESCALATE" || response.gate_status === "DENY") {
    throw new Error(
      `Constitutional block: action '${action}' blocked by gate ` +
      `${response.gate_status}. Reason: ${response.constitutional_position}. ` +
      `Triggered limits: ${response.triggered_limits.join(", ")}. ` +
      `Run: ${response.run_id}.`
    );
  }
}

// ---- Example usage in a React component ----

/*
import { useState } from "react";
import { chat, type ChatResponse } from "@/lib/cassandra";

export function Copilot() {
  const [messages, setMessages] = useState<ChatResponse[]>([]);
  const [input, setInput] = useState("");

  async function send() {
    const response = await chat(input, { page: "/copilot" });
    setMessages([...messages, response]);
    setInput("");
  }

  return (
    <div>
      {messages.map((m) => (
        <div key={m.run_id}>
          <p>{m.response}</p>
          <small>
            gate: {m.gate_status} · epistemic: {m.epistemic} ·
            route: {m.route_used} · {m.needs_operator ? "⚠️ needs operator" : ""}
          </small>
        </div>
      ))}
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={send}>Send</button>
    </div>
  );
}
*/
