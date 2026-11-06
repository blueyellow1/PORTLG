"""Tests for the wallet-authenticated Paid Access foundation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eth_account import Account
from eth_account.messages import encode_defunct

from backend import app as backend_module
from backend import paid_access


class TestPaidAccessAuthentication(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(
            paid_access, "DB_PATH", Path(self.temp_dir.name) / "paid_access.sqlite3"
        )
        self.db_patch.start()
        backend_module.app.config.update(TESTING=True)
        self.client = backend_module.app.test_client()
        self.account = Account.create()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_signed_wallet_starts_seven_day_trial_with_ten_credits(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        )
        self.assertEqual(challenge.status_code, 200)
        challenge_data = challenge.get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge_data["message"]), self.account.key
        )
        verified = self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge_data["nonce"],
                "signature": signed.signature.hex(),
            },
        )
        self.assertEqual(verified.status_code, 200)
        body = verified.get_json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["account"]["creditsRemaining"], 10)
        self.assertTrue(body["account"]["trialActive"])
        self.assertTrue(body["account"]["accessAllowed"])
        self.assertEqual(
            body["account"]["trialEndsAt"] - body["account"]["trialStartedAt"],
            7 * 24 * 60 * 60,
        )

        status = self.client.get(
            "/api/paid-access/status",
            headers={"Authorization": f"Bearer {body['token']}"},
        )
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.get_json()["account"]["wallet"], self.account.address)

    def test_invalid_signature_is_rejected(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        other = Account.create()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), other.key
        )
        response = self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_malformed_signature_returns_401_instead_of_server_error(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        response = self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": "not-a-valid-signature",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("signature is invalid", response.get_json()["error"])

    def test_transaction_confirmation_rejects_malformed_hash(self):
        response = self.client.post(
            "/api/transactions/confirm",
            json={
                "transactionHash": "0x" + "zz" * 32,
                "action": "protectedAction",
                "from": self.account.address,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("transaction hash", response.get_json()["error"])

    def _login_headers(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        login = self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        ).get_json()
        return {"Authorization": f"Bearer {login['token']}"}

    def _mock_confirm_chain(self, chain_id=420420777, calldata="0x12345678",
                            receipt_block=250, head_block=250, canonical=True):
        block_hash = "0x" + "11" * 32
        receipt_hash = block_hash if canonical else "0x" + "22" * 32
        sender = self.account.address

        class FakeFunction:
            def _encode_transaction_data(self):
                return "0x12345678"

        class FakeFunctions:
            def protectedAction(self):
                return FakeFunction()

        class FakeContract:
            functions = FakeFunctions()

            def decode_function_input(self, data):
                return type("DecodedFunction", (), {"fn_name": "protectedAction"})(), {}

        class FakeEth:
            block_number = head_block

            def get_transaction(self, tx_hash):
                return {
                    "to": backend_module.CONTRACT_ADDRESS,
                    "from": sender,
                    "chainId": chain_id,
                    "value": 0,
                    "input": calldata,
                }

            def get_transaction_receipt(self, tx_hash):
                return {
                    "status": 1,
                    "blockNumber": receipt_block,
                    "gasUsed": 50000,
                    "blockHash": receipt_hash,
                }

            def get_block(self, block_number):
                return {"hash": block_hash}

        fake_web3 = type("FakeWeb3", (), {"eth": FakeEth()})()
        return patch.object(backend_module, "rpc_ready"), patch.object(
            backend_module, "w3", fake_web3
        ), patch.object(backend_module, "get_contract", return_value=FakeContract())

    def test_confirm_transaction_rejects_wrong_chain_id(self):
        headers = self._login_headers()
        p1, p2, p3 = self._mock_confirm_chain(chain_id=1)
        with p1, p2, p3:
            response = self.client.post(
                "/api/transactions/confirm",
                json={"transactionHash": "0x" + "ab" * 32,
                      "action": "protectedAction", "from": self.account.address},
                headers=headers,
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("wrong network", response.get_json()["error"])

    def test_confirm_transaction_rejects_unexpected_calldata(self):
        headers = self._login_headers()
        p1, p2, p3 = self._mock_confirm_chain(calldata="0xdeadbeef")
        with p1, p2, p3:
            response = self.client.post(
                "/api/transactions/confirm",
                json={"transactionHash": "0x" + "ab" * 32,
                      "action": "protectedAction", "from": self.account.address},
                headers=headers,
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("calldata", response.get_json()["error"])

    def test_confirm_transaction_waits_for_required_confirmations(self):
        headers = self._login_headers()
        p1, p2, p3 = self._mock_confirm_chain(head_block=250, receipt_block=250)
        with patch.object(backend_module, "MIN_TX_CONFIRMATIONS", 2), p1, p2, p3:
            response = self.client.post(
                "/api/transactions/confirm",
                json={"transactionHash": "0x" + "ab" * 32,
                      "action": "protectedAction", "from": self.account.address},
                headers=headers,
            )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["status"], "pending")
        self.assertEqual(response.get_json()["confirmations"], 1)

    def test_confirm_transaction_rejects_noncanonical_receipt(self):
        headers = self._login_headers()
        p1, p2, p3 = self._mock_confirm_chain(canonical=False)
        with p1, p2, p3:
            response = self.client.post(
                "/api/transactions/confirm",
                json={"transactionHash": "0x" + "ab" * 32,
                      "action": "protectedAction", "from": self.account.address},
                headers=headers,
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("canonical chain", response.get_json()["error"])

    def test_confirm_transaction_consumes_credit_after_validated_receipt(self):
        headers = self._login_headers()
        p1, p2, p3 = self._mock_confirm_chain(head_block=251, receipt_block=250)
        with patch.object(backend_module, "MIN_TX_CONFIRMATIONS", 2), p1, p2, p3:
            response = self.client.post(
                "/api/transactions/confirm",
                json={"transactionHash": "0x" + "ab" * 32,
                      "action": "protectedAction", "from": self.account.address},
                headers=headers,
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["confirmed"])
        self.assertEqual(response.get_json()["confirmations"], 2)
        self.assertEqual(response.get_json()["paidAccess"]["account"]["creditsRemaining"], 9)

    def test_challenge_cannot_be_reused(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        payload = {
            "wallet": self.account.address,
            "nonce": challenge["nonce"],
            "signature": signed.signature.hex(),
        }
        self.assertEqual(self.client.post("/api/paid-access/verify", json=payload).status_code, 200)
        self.assertEqual(self.client.post("/api/paid-access/verify", json=payload).status_code, 401)

    def test_credit_is_consumed_once_per_confirmed_transaction(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        login = self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        ).get_json()
        tx_hash = "0x" + "ab" * 32
        first = paid_access.consume_credit(self.account.address, tx_hash)
        self.assertTrue(first["consumed"])
        self.assertEqual(first["account"]["creditsRemaining"], 9)
        second = paid_access.consume_credit(self.account.address, tx_hash)
        self.assertFalse(second["consumed"])
        self.assertEqual(second["reason"], "transaction_already_used")
        status = self.client.get(
            "/api/paid-access/status",
            headers={"Authorization": f"Bearer {login['token']}"},
        ).get_json()
        self.assertEqual(status["account"]["creditsRemaining"], 9)

    def test_locked_account_cannot_consume_credit(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        )
        self.assertTrue(paid_access.lock_account(self.account.address, 10, "test fraud signal"))
        result = paid_access.consume_credit(self.account.address, "0x" + "cd" * 32)
        self.assertFalse(result["consumed"])
        self.assertEqual(result["reason"], "account_locked")

    def test_status_requires_valid_session(self):
        response = self.client.get("/api/paid-access/status")
        self.assertEqual(response.status_code, 401)


    def test_five_invalid_signatures_temporarily_rate_limit_ip(self):
        for attempt in range(5):
            challenge = self.client.post(
                "/api/paid-access/challenge", json={"wallet": self.account.address}
            ).get_json()
            other = Account.create()
            signed = Account.sign_message(
                encode_defunct(text=challenge["message"]), other.key
            )
            response = self.client.post(
                "/api/paid-access/verify",
                json={
                    "wallet": self.account.address,
                    "nonce": challenge["nonce"],
                    "signature": signed.signature.hex(),
                },
            )
            self.assertIn(response.status_code, (401, 429))
        blocked = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertGreater(blocked.get_json()["retryAfterSeconds"], 0)

    def test_locked_wallet_can_recover_by_signing_fresh_challenge(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        )
        self.assertTrue(paid_access.lock_account(self.account.address, 30, "test"))
        recovery = self.client.post(
            "/api/paid-access/recovery/challenge",
            json={"wallet": self.account.address},
        )
        self.assertEqual(recovery.status_code, 200)
        recovery_data = recovery.get_json()
        recovery_signature = Account.sign_message(
            encode_defunct(text=recovery_data["message"]), self.account.key
        )
        recovered = self.client.post(
            "/api/paid-access/recovery/verify",
            json={
                "wallet": self.account.address,
                "nonce": recovery_data["nonce"],
                "signature": recovery_signature.signature.hex(),
            },
        )
        self.assertEqual(recovered.status_code, 200)
        self.assertTrue(recovered.get_json()["recovered"])
        self.assertFalse(recovered.get_json()["account"]["locked"])

    def test_recovery_challenge_cannot_be_reused(self):
        challenge = self.client.post(
            "/api/paid-access/challenge", json={"wallet": self.account.address}
        ).get_json()
        signed = Account.sign_message(
            encode_defunct(text=challenge["message"]), self.account.key
        )
        self.client.post(
            "/api/paid-access/verify",
            json={
                "wallet": self.account.address,
                "nonce": challenge["nonce"],
                "signature": signed.signature.hex(),
            },
        )
        paid_access.lock_account(self.account.address, 30, "test")
        recovery = self.client.post(
            "/api/paid-access/recovery/challenge",
            json={"wallet": self.account.address},
        ).get_json()
        recovery_signature = Account.sign_message(
            encode_defunct(text=recovery["message"]), self.account.key
        )
        payload = {
            "wallet": self.account.address,
            "nonce": recovery["nonce"],
            "signature": recovery_signature.signature.hex(),
        }
        self.assertEqual(self.client.post("/api/paid-access/recovery/verify", json=payload).status_code, 200)
        self.assertEqual(self.client.post("/api/paid-access/recovery/verify", json=payload).status_code, 401)


if __name__ == "__main__":
    unittest.main()
