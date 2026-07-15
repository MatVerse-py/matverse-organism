"""
Tests for the Epistemic state machine and belief-combination algebra
(matverse.epistemic).

Covers:
  - 8 EpistemicState values
  - Dempster-Shafer with conflict preservation
  - IRC (Índice de Resolução Cognitiva)
  - Dung preferred extensions
  - Ω-Gate evaluation
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from matverse.epistemic import (
    EpistemicState, EpistemicPolicy, SourceMetadata, Evidence,
    BeliefRecord, dempster_combine, irc, attack_graph,
    dung_preferred_extensions, evaluate_gate, GateDecision,
)


def make_evidence(id_: str, hyp: str, strength: float,
                  source_type: str = "observation",
                  independence: float = 0.9) -> Evidence:
    return Evidence(
        id=id_, content=id_,
        metadata=SourceMetadata(source_type=source_type,
                                independence_score=independence),
        hypothesis_id=hyp, strength=strength,
    )


class TestEpistemicState(unittest.TestCase):
    def test_eight_states(self):
        self.assertEqual(len(list(EpistemicState)), 8)
        names = [s.name for s in EpistemicState]
        self.assertIn("NULL", names)
        self.assertIn("OBS", names)
        self.assertIn("INF", names)
        self.assertIn("HYP", names)
        self.assertIn("EVD", names)
        self.assertIn("ADM", names)
        self.assertIn("CON", names)
        self.assertIn("ESCALATE", names)


class TestDempsterShafer(unittest.TestCase):
    def setUp(self):
        self.policy = EpistemicPolicy(id="test", version="1.0", domain="general")

    def test_empty_returns_null(self):
        b, u, c, st = dempster_combine([], self.policy)
        self.assertEqual(st, EpistemicState.NULL)
        self.assertEqual(b, 0.5)
        self.assertEqual(u, 0.5)

    def test_single_evidence_high_strength(self):
        ev = make_evidence("e1", "h1", strength=0.95)
        b, u, c, st = dempster_combine([ev], self.policy)
        self.assertGreater(b, 0.9)
        self.assertEqual(st, EpistemicState.CON)

    def test_conflicting_evidence_escalates(self):
        ev1 = make_evidence("e1", "h1", strength=0.9)
        ev2 = make_evidence("e2", "h1", strength=0.1)
        b, u, c, st = dempster_combine([ev1, ev2], self.policy)
        # Strong conflict should push to ESCALATE
        self.assertEqual(st, EpistemicState.ESCALATE)
        self.assertEqual(c, 1.0)

    def test_consistent_evidence_state_progression(self):
        ev1 = make_evidence("e1", "h1", strength=0.7)
        ev2 = make_evidence("e2", "h1", strength=0.8)
        b, u, c, st = dempster_combine([ev1, ev2], self.policy)
        # Two moderately confident evidences
        self.assertGreater(b, 0.5)
        self.assertNotEqual(st, EpistemicState.NULL)
        self.assertNotEqual(st, EpistemicState.ESCALATE)


class TestIRC(unittest.TestCase):
    def test_irc_at_max_belief(self):
        # IRC = 1 - H/log(2); at p=1 the entropy H is 0
        self.assertAlmostEqual(irc(1.0, 0.0), 1.0, places=3)

    def test_irc_at_high_belief(self):
        # At p=0.99, H ≈ 0.056, IRC ≈ 0.919
        self.assertAlmostEqual(irc(0.99, 0.01), 0.919, places=2)

    def test_irc_at_min_belief(self):
        self.assertAlmostEqual(irc(0.5, 0.5), 0.0, places=3)

    def test_irc_clamped(self):
        # Out-of-range high clamps to 1.0
        self.assertEqual(irc(1.5, 0.0), 1.0)
        # Out-of-range low clamps to 0.0
        self.assertEqual(irc(-0.1, 0.0), 0.0)


class TestDungExtensions(unittest.TestCase):
    def test_no_conflict_one_extension(self):
        policy = EpistemicPolicy(id="t", version="1.0", domain="general",
                                  conflict_threshold=0.9)
        # OVERLAPPING evidence (e_shared) so Jaccard > 0.9 → no attack
        recs = {
            "h1": BeliefRecord(id="h1", evidence_ids=["e1", "e_shared"]),
            "h2": BeliefRecord(id="h2", evidence_ids=["e2", "e_shared"]),
        }
        evid = {
            "e1": make_evidence("e1", "h1", 0.8),
            "e2": make_evidence("e2", "h2", 0.8),
            "e_shared": make_evidence("e_shared", "h1", 0.7),
        }
        # Patch: e_shared is also evidence for h1 only (not h2's pool of evidence_ids)
        # Re-declare h2 with both
        recs["h2"] = BeliefRecord(id="h2", evidence_ids=["e2", "e_shared"])
        prefs = dung_preferred_extensions(recs, evid, policy)
        # With overlapping evidence, the conflict is low → no attack → one big extension
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0], {"h1", "h2"})

    def test_full_conflict_two_extensions(self):
        policy = EpistemicPolicy(id="t", version="1.0", domain="general",
                                  conflict_threshold=0.1)
        recs = {
            "h1": BeliefRecord(id="h1", evidence_ids=["e1"]),
            "h2": BeliefRecord(id="h2", evidence_ids=["e2"]),
        }
        evid = {
            "e1": make_evidence("e1", "h1", 0.8),
            "e2": make_evidence("e2", "h2", 0.8),
        }
        prefs = dung_preferred_extensions(recs, evid, policy)
        # They attack each other = two singleton preferred extensions
        self.assertEqual(len(prefs), 2)
        self.assertIn({"h1"}, prefs)
        self.assertIn({"h2"}, prefs)


class TestEvaluateGate(unittest.TestCase):
    def test_hold_decision(self):
        policy = EpistemicPolicy(id="t", version="1.0", domain="general",
                                  work_cap=10.0)
        rec = BeliefRecord(id="h1", work_spent=0.5)  # below work_cap/2
        evid = [make_evidence("e1", "h1", 0.8)]
        decision = evaluate_gate(rec, evid, policy)
        self.assertEqual(decision.decision, "HOLD")
        self.assertIn("insufficient work", decision.reason)

    def test_admissible_decision(self):
        policy = EpistemicPolicy(id="t", version="1.0", domain="general",
                                  work_cap=10.0, entropy_max=0.5,
                                  null_max=0.3, irc_min=0.5)
        rec = BeliefRecord(id="h1", work_spent=8.0)  # ≥ work_cap/2
        evid = [make_evidence("e1", "h1", 0.95)]
        decision = evaluate_gate(rec, evid, policy)
        self.assertEqual(decision.decision, "ADMISSIBLE")
        self.assertEqual(decision.state, EpistemicState.ADM)

    def test_escalate_decision(self):
        policy = EpistemicPolicy(id="t", version="1.0", domain="general",
                                  work_cap=10.0)
        rec = BeliefRecord(id="h1", work_spent=8.0)
        # Two conflicting evidences
        evid = [make_evidence("e1", "h1", 0.95),
                make_evidence("e2", "h1", 0.05)]
        decision = evaluate_gate(rec, evid, policy)
        self.assertEqual(decision.decision, "ESCALATE")
        self.assertEqual(decision.state, EpistemicState.ESCALATE)


if __name__ == "__main__":
    unittest.main()
