"""End-to-end test of the FullOrganismRunner (v3.6.0)."""
import unittest
from matverse import (
    FullOrganismRunner, Problem, Hypothesis,
)


def _full_problem() -> Problem:
    return Problem(
        id="P_RUN", objective="how to test the full organism runner",
        scope="test", constraints=[], stakeholders=["tester"],
        hypotheses=[
            Hypothesis(
                id="H_OFFLINE", claim="offline approach wins",
                variables={"v": 1.0}, evidence_for=["e1"],
                evidence_against=["c1"], falsification_criteria="v < 0.5",
                cost_estimate=10.0, expected_value=200.0,
                risk=0.2, reversibility=0.9, lineage=["v3.0.0"],
            ),
            Hypothesis(
                id="H_PROMISE", claim="promise approach wins",
                variables={"v": 5.0}, evidence_for=["e2"],
                evidence_against=["c2"], falsification_criteria="v < 0.5",
                cost_estimate=5.0, expected_value=400.0,
                risk=0.7, reversibility=0.3, lineage=["v3.0.0"],
            ),
        ],
        metadata={
            "science_origin": "test", "contract": "schema/v3",
            "ecosystem_impact": "none", "lineage": ["v3.0.0"],
        },
    )


class TestFullRunner(unittest.TestCase):

    def test_full_organism_run_produces_closure(self):
        r = FullOrganismRunner()
        result = r.run(_full_problem())
        # Closure
        self.assertTrue(result.closure.closure_id.startswith("MV-CLOSURE-"))
        self.assertIn(result.closure.state_closure, {"CLOSED", "REPLAYED_INDEPENDENT"})
        # SVCA
        self.assertEqual(result.svca.status, "PASS")
        # Cassandra
        self.assertEqual(result.cassandra_reading["problem_id"], "P_RUN")
        # Organism
        self.assertIn("decision", result.organism_report)
        # Publication prepared
        self.assertEqual(result.publication["zenodo"]["status"],
                         "PREPARED_NOT_PUBLISHED")
        self.assertEqual(result.publication["github"]["status"],
                         "PREPARED_NOT_RELEASED")
        self.assertEqual(result.publication["huggingface"]["status"],
                         "PREPARED_NOT_PUBLISHED")
        self.assertEqual(result.publication["blockchain"]["status"],
                         "PREPARED_NOT_BROADCAST")
        # Replay
        self.assertIn(result.replay_report["matches"], (True, False))
        # M-bit
        self.assertIsNotNone(result.mbit)
        # Atlas snapshot
        self.assertIn("nodes", result.atlas_snapshot)

    def test_organism_picks_safer_hypothesis(self):
        r = FullOrganismRunner()
        result = r.run(_full_problem())
        top = result.organism_report["ranked"][0]
        # H_OFFLINE is safer; should be ranked first
        self.assertEqual(top["id"], "H_OFFLINE")

    def test_atlas_records_canonical_organs(self):
        r = FullOrganismRunner()
        result = r.run(_full_problem())
        kinds = {n["kind"] for n in result.atlas_snapshot["nodes"]}
        self.assertIn("organ", kinds)
        self.assertIn("capability", kinds)
        self.assertIn("svca", kinds)
        self.assertIn("closure", kinds)

    def test_canonical_hash_is_stable_for_same_bundle(self):
        # canonical_hash() must be deterministic for the same instance.
        r = FullOrganismRunner()
        result = r.run(_full_problem(), closure_title="X",
                        closure_parent="PARENT-1", repository="repo",
                        commit="c1", release_tag="v3.6.0")
        h1 = result.closure.canonical_hash()
        h2 = result.closure.canonical_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
