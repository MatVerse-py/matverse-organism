"""
Tests for the Cassandra agent (matverse.cassandra_agent).

Covers:
  - Constitutional system prompt: the 4 layers (ROLE, SCOPE,
    ADMISSIBILITY, EPITEMIC, CANONICAL_CORPUS) are present.
  - Standalone interpreter:
    - "o que é omega" → mentions the canonical 0.81 and tests/test_omega.py
    - "o que é MNB" → mentions the 5-tuple and the lineage (MNB posterior)
    - "o que é GTHDL" → mentions the master equation
    - "execute / publique / assine" → fail-closed (ESCALATE)
    - "rode X" → routes to URANO (HOLD / PROTOTYPE)
    - "crie hipótese sobre X" → routes to COG (HYP)
  - Epistemic tag parser
  - Gate status classifier
  - Base44 client (mocked, no real network)
  - CassandraAgent: full flow in standalone mode
  - Constitutional boundaries: NEVER authorizes external action
"""
import json
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.cassandra_agent import (
    CASSANDRA_SYSTEM_PROMPT, CassandraAgent, CassandraRun, local_interpret,
)
from matverse.cassandra_base44 import (
    Base44Client, Base44Error, SessionToken, CapabilityToken,
    DEFAULT_APP_ID, API_KEY_ENV,
)
from matverse.cassandra_agent import (  # noqa: F811  (re-import for clarity)
    CASSANDRA_SYSTEM_PROMPT, ROLE, SCOPE, ADMISSIBILITY,
    EPITEMIC, CANONICAL_CORPUS, local_interpret,
    Base44Client, Base44Error, CassandraAgent, CassandraRun,
    DEFAULT_APP_ID,
)


class TestConstitutionalPrompt(unittest.TestCase):
    def test_role_is_not_sovereign_ai(self):
        self.assertIn("NÃO é", ROLE)
        self.assertIn("operador cognitivo", ROLE)

    def test_scope_has_4_boundaries(self):
        self.assertIn("ADMISSIBILITY_BOUNDARY", SCOPE)
        self.assertIn("EVIDENCE_POLICY", SCOPE)
        self.assertIn("REPLAY_POLICY", SCOPE)
        self.assertIn("NEVER_AUTHORIZES_EXTERNAL_ACTION", SCOPE)

    def test_admissibility_fail_closed(self):
        self.assertIn("ESCALATE", ADMISSIBILITY)
        self.assertIn("fail-closed", ADMISSIBILITY)

    def test_epistemic_8_states(self):
        for state in ("OBS", "INF", "HYP", "EVD", "ADM", "CON", "ESC", "BLOCK"):
            self.assertIn(state, EPITEMIC)

    def test_canon_has_6_invariants(self):
        self.assertIn("Coerência crescente não é evidência crescente", CANONICAL_CORPUS)
        self.assertIn("MNB não é pai de Captals", CANONICAL_CORPUS)
        self.assertIn("Cassandra é time de skills", CANONICAL_CORPUS)
        self.assertIn("organismo prepara, o operador assina, o mundo testemunha", CANONICAL_CORPUS)
        self.assertIn("PREPARED_NOT_PUBLISHED", CANONICAL_CORPUS)
        self.assertIn("Falha-fechado", CANONICAL_CORPUS)

    def test_full_prompt_assembled(self):
        # Should contain the role, scope, admissibility, epistemic, canon
        self.assertIn("operador cognitivo", CASSANDRA_SYSTEM_PROMPT)
        self.assertIn("ADMISSIBILITY_BOUNDARY", CASSANDRA_SYSTEM_PROMPT)
        self.assertIn("epistemic: <OBS", CASSANDRA_SYSTEM_PROMPT)
        self.assertIn("Coerência crescente", CASSANDRA_SYSTEM_PROMPT)
        # And be non-trivial
        self.assertGreater(len(CASSANDRA_SYSTEM_PROMPT), 1500)


class TestLocalInterpreter(unittest.TestCase):
    def test_omega_explanation_uses_canonical(self):
        out = local_interpret("o que é omega score?")
        self.assertIn("0.81", out)
        self.assertIn("test_omega.py", out)
        self.assertIn("epistemic: OBS", out)

    def test_mnb_explanation_mentions_5tuple_and_lineage(self):
        out = local_interpret("o que é MNB?")
        self.assertIn("(e, Ψ, C, τ, h)", out)
        self.assertIn("MNB é camada POSTERIOR", out)
        self.assertIn("Captals", out)
        self.assertIn("epistemic: OBS", out)

    def test_gthdl_explanation_mentions_master_equation(self):
        out = local_interpret("o que é GTHDL?")
        self.assertIn("dρ/dt = -i[Ĥ_Σ, ρ]", out)
        self.assertIn("Ĥ_Σ = λ_Ω·Ω̂", out)
        self.assertIn("epistemic: OBS", out)

    def test_riemannian_manifold_explanation(self):
        out = local_interpret("explique o manifold Riemanniano")
        self.assertIn("M = (O, R, g, Φ, ρ)", out)
        self.assertIn("epistemic: OBS", out)

    def test_captals_uses_lineage_correction(self):
        out = local_interpret("o que é Captals?")
        self.assertIn("gênese", out)
        self.assertIn("camada posterior", out)  # MNB is later layer (corpus correction)

    def test_cassandra_self_description(self):
        out = local_interpret("explique Cassandra")
        self.assertIn("modelo informacional", out)
        self.assertIn("7 skills", out)
        self.assertIn("4 de 7", out)
        self.assertIn("3 HOLD", out)

    def test_external_action_fails_closed(self):
        for kw in ("execute", "publique", "assine", "transfira", "deploy agora"):
            out = local_interpret(f"por favor, {kw} agora")
            self.assertIn("fora do escopo", out)
            self.assertIn("ESC", out)

    def test_run_routes_to_urano(self):
        out = local_interpret("rode o experimento 4")
        self.assertIn("URANO", out)
        self.assertIn("PROTOTYPE", out)

    def test_create_routes_to_cog(self):
        out = local_interpret("crie hipótese sobre o experimento 4")
        self.assertIn("COG", out)
        self.assertIn("HYP", out)

    def test_generic_input_returns_hyp(self):
        out = local_interpret("olá, tudo bem?")
        self.assertIn("epistemic: HYP", out)

    def test_always_suggests_upgradeable(self):
        out = local_interpret("qualquer coisa")
        self.assertIn("OBS", out)
        self.assertIn("evidência", out)


class TestCassandraRun(unittest.TestCase):
    def test_construction(self):
        r = CassandraRun(
            run_id="r1", conversation_id="c1", user_message="x",
            cassandra_response="[epistemic: OBS] answer",
            epistemic_classification="OBS",
            gate_status="PASS", created_at=0, used_base44=False,
        )
        self.assertEqual(r.run_id, "r1")
        d = r.to_dict()
        self.assertEqual(d["run_id"], "r1")
        self.assertEqual(d["gate_status"], "PASS")
        self.assertFalse(d["used_base44"])


class TestBase44Client(unittest.TestCase):
    def test_unconfigured_returns_false(self):
        c = Base44Client(api_key="")
        # No api_key and no session → not configured, not authenticated
        self.assertFalse(c.is_configured)
        self.assertFalse(c.is_authenticated)

    def test_configured_with_env(self):
        with patch.dict(os.environ, {"BASE44_API_KEY": "fake-key-123"}):
            c = Base44Client()
            # configured because the api_key is in memory at this point
            self.assertTrue(c.is_configured)
            # The key is held privately and is wiped after authenticate()
            self.assertEqual(c._api_key, "fake-key-123")

    def test_unconfigured_request_raises(self):
        c = Base44Client(api_key="")
        with self.assertRaises(Base44Error):
            c.list_entities("SGIMetric")

    def test_authenticate_wipes_api_key(self):
        """After authenticate(), the api_key is wiped from memory and
        a SessionToken replaces it. This is the security invariant."""
        with patch.dict(os.environ, {"BASE44_API_KEY": "fake-key"}):
            c = Base44Client()
            self.assertEqual(c._api_key, "fake-key")
            now = int(time.time())
            payload = json.dumps({"token": "sess-1", "issued_at": now,
                                  "ttl_seconds": 3600, "user_id": "u1"}).encode()
            mock_resp = MagicMock()
            mock_resp.read.return_value = payload
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            with patch("urllib.request.urlopen", return_value=mock_resp):
                sess = c.authenticate()
            # After authenticate, the key is gone
            self.assertIsNone(c._api_key)
            self.assertIsNotNone(c.session)
            self.assertEqual(sess.token, "sess-1")
            self.assertTrue(c.is_authenticated)

    def test_request_happy_path_uses_bearer(self):
        """Entity calls use the session bearer, not the api_key header."""
        with patch.dict(os.environ, {"BASE44_API_KEY": "fake-key"}):
            c = Base44Client()
            now = int(time.time())
            sess_payload = json.dumps({"token": "sess-1", "issued_at": now,
                                       "ttl_seconds": 3600, "user_id": "u1"}).encode()
            sess_resp = MagicMock()
            sess_resp.read.return_value = sess_payload
            sess_resp.__enter__ = MagicMock(return_value=sess_resp)
            sess_resp.__exit__ = MagicMock(return_value=False)
            with patch("urllib.request.urlopen", return_value=sess_resp):
                c.authenticate()
            # Now mock the entity call
            list_resp = MagicMock()
            list_resp.read.return_value = b'[{"id":"r1","value":1}]'
            list_resp.__enter__ = MagicMock(return_value=list_resp)
            list_resp.__exit__ = MagicMock(return_value=False)
            captured_headers = {}
            def fake_urlopen(req, **kw):
                captured_headers.update(dict(req.headers))
                return list_resp
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                out = c.list_entities("SGIMetric")
            self.assertEqual(out, [{"id": "r1", "value": 1}])
            self.assertNotIn("fake-key", str(captured_headers))
            self.assertIn("Bearer sess-1", captured_headers.get("Authorization", ""))

    def test_default_app_id(self):
        self.assertEqual(DEFAULT_APP_ID, "6a2dd76b300afd3eb43293d7")

    def test_session_token_expiry(self):
        now = int(time.time())
        s = SessionToken(token="t", issued_at=now - 100, ttl_seconds=60)
        self.assertTrue(s.is_expired())
        s2 = SessionToken(token="t", issued_at=now, ttl_seconds=3600)
        self.assertFalse(s2.is_expired())

    def test_capability_token_expiry(self):
        now = int(time.time())
        c = CapabilityToken(token="t", agent_id="a", skill_name="s",
                            issued_at=now - 100, ttl_seconds=60)
        self.assertTrue(c.is_expired())
        c2 = CapabilityToken(token="t", agent_id="a", skill_name="s",
                              issued_at=now, ttl_seconds=3600)
        self.assertFalse(c2.is_expired())
        self.assertEqual(c2.to_dict()["agent_id"], "a")


class TestCassandraAgentStandalone(unittest.TestCase):
    def setUp(self):
        self.agent = CassandraAgent(mode="standalone")

    def test_mode_is_standalone(self):
        self.assertFalse(self.agent.is_base44)

    def test_chat_returns_run(self):
        run = self.agent.chat("o que é MNB?")
        self.assertIsInstance(run, CassandraRun)
        self.assertFalse(run.used_base44)
        self.assertIn("(e, Ψ, C, τ, h)", run.cassandra_response)
        self.assertEqual(run.epistemic_classification, "OBS")

    def test_chat_external_action_escalates(self):
        run = self.agent.chat("publique agora no Zenodo")
        self.assertEqual(run.gate_status, "ESCALATE")
        self.assertEqual(run.epistemic_classification, "ESC")

    def test_chat_runs_are_stored(self):
        self.assertEqual(len(self.agent.runs), 0)
        self.agent.chat("o que é omega?")
        self.agent.chat("publique agora")
        self.assertEqual(len(self.agent.runs), 2)

    def test_system_prompt_exposed(self):
        p = self.agent.system_prompt_text()
        self.assertIn("operador cognitivo", p)

    def test_run_ids_unique(self):
        r1 = self.agent.chat("teste 1")
        r2 = self.agent.chat("teste 2")
        self.assertNotEqual(r1.run_id, r2.run_id)


class TestCassandraAgentBase44(unittest.TestCase):
    def setUp(self):
        self.client = Base44Client(api_key="fake-key")
        self.agent = CassandraAgent(base44=self.client, mode="base44")

    def test_mode_is_base44(self):
        self.assertTrue(self.agent.is_base44)

    def test_chat_uses_base44(self):
        # Mock the Base44 methods
        self.client.create_conversation = MagicMock(return_value={"id": "conv-1"})
        self.client.send_message = MagicMock(return_value={"content": "Cassandra: olá! [epistemic: OBS]"})

        run = self.agent.chat("olá")
        self.assertTrue(run.used_base44)
        self.assertEqual(run.conversation_id, "conv-1")
        self.client.create_conversation.assert_called_once()
        self.client.send_message.assert_called_once()

    def test_chat_falls_back_to_local_on_error(self):
        self.client.create_conversation = MagicMock(side_effect=Base44Error("503"))
        run = self.agent.chat("o que é MNB?")
        self.assertFalse(run.used_base44)
        self.assertIn("FALLBACK", run.cassandra_response)
        # The fallback still uses local_interpret, so we get the MNB explanation
        self.assertIn("(e, Ψ, C, τ, h)", run.cassandra_response)

    def test_persist_writes_to_base44(self):
        self.client.create_conversation = MagicMock(return_value={"id": "conv-1"})
        self.client.send_message = MagicMock(return_value={"content": "oi [epistemic: OBS]"})
        self.client.create_entity = MagicMock(return_value={"id": "run-1"})
        run = self.agent.chat("hello", persist=True)
        self.assertTrue(run.used_base44)
        self.client.create_entity.assert_called_once()
        args, kwargs = self.client.create_entity.call_args
        self.assertEqual(args[0], "CassandraRun")
        self.assertEqual(args[1]["input_summary"], "hello")
        self.assertEqual(args[1]["epistemic_classification"], "OBS")

    def test_persist_silent_on_error(self):
        self.client.create_conversation = MagicMock(return_value={"id": "conv-1"})
        self.client.send_message = MagicMock(return_value={"content": "hi"})
        self.client.create_entity = MagicMock(side_effect=Base44Error("write fail"))
        # Should NOT raise
        run = self.agent.chat("hello", persist=True)
        self.assertIsNotNone(run)


class TestCassandraAgentAutoMode(unittest.TestCase):
    def test_auto_falls_back_to_standalone_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            a = CassandraAgent(mode="auto")
            self.assertEqual(a.mode, "standalone")

    def test_auto_picks_base44_with_key(self):
        with patch.dict(os.environ, {"BASE44_API_KEY": "x"}):
            a = CassandraAgent(mode="auto")
            self.assertEqual(a.mode, "base44")


if __name__ == "__main__":
    unittest.main()
