"""Backend API tests for transaction validation and preparation.

These tests mock the RPC boundary. They validate API behavior without sending
transactions to Portaldot or requiring MetaMask credentials.
"""
import unittest
from unittest.mock import MagicMock, patch

from backend import app as backend_module


class TestBackendTransactionAPI(unittest.TestCase):
    def setUp(self):
        backend_module.app.config.update(TESTING=True)
        self.client = backend_module.app.test_client()

    def make_contract(self, owner, paused=False):
        contract = MagicMock()
        contract.address = backend_module.CONTRACT_ADDRESS
        contract.functions.owner.return_value.call.return_value = owner
        contract.functions.paused.return_value.call.return_value = paused
        contract.functions.pause.return_value._encode_transaction_data.return_value = "0x8456cb59"
        contract.functions.unpause.return_value._encode_transaction_data.return_value = "0x3f4ba83a"
        contract.functions.protectedAction.return_value._encode_transaction_data.return_value = "0x3d7b369a"
        return contract

    @patch.object(backend_module, "send_from_directory", return_value="window.PORTLG_WALLET_TEST = true;")
    def test_wallet_javascript_route_serves_frontend_asset(self, send_file):
        response = self.client.get("/wallet.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PORTLG_WALLET_TEST", response.get_data(as_text=True))
        send_file.assert_called_once_with(backend_module.ROOT / "frontend", "wallet.js")

    def test_unknown_action_is_rejected(self):
        response = self.client.post(
            "/api/transactions/prepare",
            json={"action": "drainFunds", "from": "0x0000000000000000000000000000000000000001"},
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_wallet_address_is_rejected(self):
        response = self.client.post(
            "/api/transactions/prepare",
            json={"action": "pause", "from": "not-an-address"},
        )
        self.assertEqual(response.status_code, 400)

    @patch.object(backend_module, "rpc_ready")
    @patch.object(backend_module, "get_contract")
    def test_owner_pause_request_returns_unsigned_transaction(self, get_contract, rpc_ready):
        owner = "0x0000000000000000000000000000000000000001"
        get_contract.return_value = self.make_contract(owner, paused=False)
        response = self.client.post(
            "/api/transactions/prepare",
            json={"action": "pause", "from": owner},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ready"])
        self.assertEqual(body["transaction"]["from"], owner)
        self.assertEqual(body["transaction"]["data"], "0x8456cb59")
        self.assertEqual(body["transaction"]["to"], backend_module.CONTRACT_ADDRESS)

    @patch.object(backend_module, "rpc_ready")
    @patch.object(backend_module, "get_contract")
    def test_non_owner_pause_request_is_forbidden(self, get_contract, rpc_ready):
        owner = "0x0000000000000000000000000000000000000001"
        other = "0x0000000000000000000000000000000000000002"
        get_contract.return_value = self.make_contract(owner, paused=False)
        response = self.client.post(
            "/api/transactions/prepare",
            json={"action": "pause", "from": other},
        )
        self.assertEqual(response.status_code, 403)

    @patch.object(backend_module, "rpc_ready")
    @patch.object(backend_module, "get_contract")
    def test_protected_action_is_rejected_when_paused(self, get_contract, rpc_ready):
        owner = "0x0000000000000000000000000000000000000001"
        get_contract.return_value = self.make_contract(owner, paused=True)
        response = self.client.post(
            "/api/transactions/prepare",
            json={"action": "protectedAction", "from": owner},
        )
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
