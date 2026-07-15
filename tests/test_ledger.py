"""Tests for the Ledger module."""
import unittest
import tempfile
import os
from matverse.ledger import Ledger, GENESIS_HASH


class TestLedger(unittest.TestCase):

    def test_empty_chain_verifies(self):
        led = Ledger()
        v = led.verify()
        self.assertTrue(v["ok"])
        self.assertEqual(v["length"], 0)

    def test_append_chains_hashes(self):
        led = Ledger()
        r1 = led.append(kind="test", input_obj={"a": 1}, output_obj={"b": 2}, status="PASS")
        r2 = led.append(kind="test", input_obj={"a": 3}, output_obj={"b": 4}, status="PASS")
        # r2.ledger_prev must equal r1.ledger_hash
        self.assertEqual(r2.ledger_prev, r1.ledger_hash)
        v = led.verify()
        self.assertTrue(v["ok"])
        self.assertEqual(v["length"], 2)

    def test_tamper_detection(self):
        led = Ledger()
        led.append(kind="test", input_obj={"a": 1}, output_obj={"b": 2}, status="PASS")
        led.append(kind="test", input_obj={"a": 3}, output_obj={"b": 4}, status="PASS")
        # Tamper: mutate the first entry's status
        led._entries[0].status = "FAIL"
        v = led.verify()
        self.assertFalse(v["ok"])
        self.assertEqual(v["broken_at"], 0)

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "led.json")
            led = Ledger(path=path)
            led.append(kind="test", input_obj={"a": 1}, output_obj={"b": 2}, status="PASS")
            del led
            led2 = Ledger(path=path)
            led2.load()
            self.assertEqual(len(led2), 1)
            v = led2.verify()
            self.assertTrue(v["ok"])


if __name__ == "__main__":
    unittest.main()
