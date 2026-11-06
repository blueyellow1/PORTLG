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

    def test_status_requires_valid_session(self):
        response = self.client.get("/api/paid-access/status")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
