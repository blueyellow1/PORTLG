"""Local EVM tests for PORTLGuardLite.

Compile first with: python scripts/compile_contract.py
Run with: python -m unittest discover -s tests -p 'test_*.py' -v
"""
import json
import unittest
from pathlib import Path

from web3 import EthereumTesterProvider, Web3
from eth_tester.exceptions import TransactionFailed

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "build" / "PORTLGuardLite.json"


@unittest.skipUnless(ARTIFACT.is_file(), "Compile contract before running tests.")
class TestPORTLGuardLite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w3 = Web3(EthereumTesterProvider())
        artifact = json.loads(ARTIFACT.read_text())
        factory = cls.w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
        receipt = cls.w3.eth.wait_for_transaction_receipt(
            factory.constructor().transact({"from": cls.w3.eth.accounts[0]})
        )
        cls.contract = cls.w3.eth.contract(
            address=receipt.contractAddress, abi=artifact["abi"]
        )
        cls.owner = cls.w3.eth.accounts[0]
        cls.other = cls.w3.eth.accounts[1]

    def setUp(self):
        # Restore the contract to the active state before each independent test.
        if self.contract.functions.paused().call():
            self.contract.functions.unpause().transact({"from": self.owner})

    def test_deployer_is_owner_and_initial_state_is_active(self):
        self.assertEqual(self.contract.functions.owner().call(), self.owner)
        self.assertFalse(self.contract.functions.paused().call())

    def test_only_owner_can_pause(self):
        with self.assertRaises(TransactionFailed):
            self.contract.functions.pause().transact({"from": self.other})
        self.contract.functions.pause().transact({"from": self.owner})
        self.assertTrue(self.contract.functions.paused().call())

    def test_only_owner_can_unpause(self):
        self.contract.functions.pause().transact({"from": self.owner})
        with self.assertRaises(TransactionFailed):
            self.contract.functions.unpause().transact({"from": self.other})
        self.contract.functions.unpause().transact({"from": self.owner})
        self.assertFalse(self.contract.functions.paused().call())

    def test_protected_action_emits_security_alert(self):
        receipt = self.contract.functions.protectedAction().transact({"from": self.other})
        logs = self.contract.events.SecurityAlert().process_receipt(
            self.w3.eth.wait_for_transaction_receipt(receipt)
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["args"]["user"], self.other)
        self.assertEqual(logs[0]["args"]["action"], "Protected action executed")

    def test_protected_action_reverts_while_paused(self):
        self.contract.functions.pause().transact({"from": self.owner})
        with self.assertRaises(TransactionFailed):
            self.contract.functions.protectedAction().transact({"from": self.other})


if __name__ == "__main__":
    unittest.main()
