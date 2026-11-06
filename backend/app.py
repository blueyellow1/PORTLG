"""PORTLG application backend.

The backend validates requested contract operations and prepares unsigned
transactions. MetaMask remains responsible for user approval and signing.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from web3 import Web3

from backend import paid_access

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

RPC_URL = os.getenv("RPC_URL", "https://test-evm-rpc-v3.portaldot.dev")
CONTRACT_ADDRESS = Web3.to_checksum_address(
    os.getenv("CONTRACT_ADDRESS", "0x44406CD3e7cce420c316D015FEE74303F16629E5")
)
CHAIN_ID = int(os.getenv("CHAIN_ID", "420420777"))
EVENTS_FROM_BLOCK = int(os.getenv("EVENTS_FROM_BLOCK", "200580"))
BUILD = ROOT / "build" / "PORTLGuardLite.json"
ABI = json.loads(BUILD.read_text())["abi"] if BUILD.exists() else []

app = Flask(__name__)
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))

ALLOWED_ACTIONS = {"pause", "unpause", "protectedAction"}


def get_contract():
    if not ABI:
        raise RuntimeError("Contract ABI is missing. Run python scripts/compile_contract.py first.")
    return w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)


def rpc_ready():
    if not w3.is_connected():
        raise ConnectionError("Unable to connect to the configured Portaldot V3 RPC endpoint.")
    actual_chain_id = w3.eth.chain_id
    if actual_chain_id != CHAIN_ID:
        raise ConnectionError(
            f"RPC chain ID mismatch: expected {CHAIN_ID}, received {actual_chain_id}."
        )


def _session_account():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    return paid_access.get_session_account(authorization[7:])


@app.get("/")
def index():
    return send_from_directory(ROOT / "frontend", "index.html")


@app.get("/wallet.js")
def wallet_script():
    return send_from_directory(ROOT / "frontend", "wallet.js")


@app.get("/api/health")
def health():
    try:
        rpc_ready()
        return jsonify(service="PORTLG backend", rpcConnected=True, chainId=CHAIN_ID)
    except Exception as exc:
        return jsonify(service="PORTLG backend", rpcConnected=False, error=str(exc)), 503


@app.get("/api/config")
def config():
    return jsonify(address=CONTRACT_ADDRESS, chainId=CHAIN_ID)


@app.post("/api/paid-access/challenge")
def paid_access_challenge():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(paid_access.create_challenge(payload.get("wallet")))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/paid-access/verify")
def paid_access_verify():
    payload = request.get_json(silent=True) or {}
    try:
        result = paid_access.verify_signature(
            payload.get("wallet"), payload.get("nonce"), payload.get("signature")
        )
        return jsonify(authenticated=True, **result)
    except PermissionError as exc:
        return jsonify(error=str(exc)), 423
    except ValueError as exc:
        return jsonify(error=str(exc)), 401


@app.get("/api/paid-access/status")
def paid_access_status():
    account = _session_account()
    if not account:
        return jsonify(error="A valid PORTLG wallet session is required."), 401
    return jsonify(account=account)


@app.get("/api/status")
def status():
    try:
        rpc_ready()
        contract = get_contract()
        return jsonify(
            connected=True,
            address=contract.address,
            owner=contract.functions.owner().call(),
            paused=contract.functions.paused().call(),
            block=w3.eth.block_number,
            chainId=w3.eth.chain_id,
        )
    except Exception as exc:
        return jsonify(error=str(exc)), 503


@app.post("/api/transactions/prepare")
def prepare_transaction():
    """Validate an operation and return calldata for MetaMask to sign.

    This endpoint never signs or broadcasts a transaction and never receives
    a private key. The connected MetaMask account is the transaction sender.
    """
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    sender = payload.get("from")

    if action not in ALLOWED_ACTIONS:
        return jsonify(error="Unsupported contract action."), 400
    if not isinstance(sender, str) or not Web3.is_address(sender):
        return jsonify(error="A valid connected wallet address is required."), 400

    try:
        rpc_ready()
        contract = get_contract()
        sender = Web3.to_checksum_address(sender)
        owner = Web3.to_checksum_address(contract.functions.owner().call())
        paused = contract.functions.paused().call()

        if action in {"pause", "unpause"} and sender != owner:
            return jsonify(error="Only the contract owner can perform this operation."), 403
        if action == "pause" and paused:
            return jsonify(error="The contract is already paused."), 409
        if action == "unpause" and not paused:
            return jsonify(error="The contract is not paused."), 409
        if action == "protectedAction" and paused:
            return jsonify(error="The protected action is unavailable while the contract is paused."), 409

        function = getattr(contract.functions, action)()
        calldata = function._encode_transaction_data()

        return jsonify(
            ready=True,
            action=action,
            transaction={
                "from": sender,
                "to": CONTRACT_ADDRESS,
                "data": calldata,
                "value": "0x0",
                "chainId": hex(CHAIN_ID),
            },
            message="Transaction prepared. Review and approve it in MetaMask.",
        )
    except Exception as exc:
        app.logger.exception("Transaction preparation failed")
        return jsonify(error=str(exc)), 503


@app.post("/api/transactions/confirm")
def confirm_transaction():
    """Verify a submitted transaction and its successful on-chain receipt."""
    payload = request.get_json(silent=True) or {}
    tx_hash = payload.get("transactionHash")
    expected_action = payload.get("action")
    expected_sender = payload.get("from")

    if not isinstance(tx_hash, str) or not Web3.is_hex(tx_hash) or len(tx_hash) != 66:
        return jsonify(error="A valid transaction hash is required."), 400
    if expected_action not in ALLOWED_ACTIONS:
        return jsonify(error="Unsupported contract action."), 400
    if not isinstance(expected_sender, str) or not Web3.is_address(expected_sender):
        return jsonify(error="A valid wallet address is required."), 400

    try:
        rpc_ready()
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if Web3.to_checksum_address(tx["to"]) != CONTRACT_ADDRESS:
            return jsonify(error="Transaction destination does not match PORTLGuardLite."), 400
        if Web3.to_checksum_address(tx["from"]) != Web3.to_checksum_address(expected_sender):
            return jsonify(error="Transaction sender does not match the connected wallet."), 400
        if receipt["status"] != 1:
            return jsonify(confirmed=False, status="failed", transactionHash=tx_hash), 409

        contract = get_contract()
        function, params = contract.decode_function_input(tx["input"])
        if function.fn_name != expected_action:
            return jsonify(error="Confirmed transaction does not match the requested action."), 400

        return jsonify(
            confirmed=True,
            status="success",
            action=function.fn_name,
            transactionHash=tx_hash,
            blockNumber=receipt["blockNumber"],
            gasUsed=receipt["gasUsed"],
        )
    except Exception as exc:
        app.logger.exception("Transaction confirmation failed")
        return jsonify(error=str(exc)), 503


@app.get("/api/events")
def events():
    try:
        rpc_ready()
        contract = get_contract()
        items = []
        for name in ("SecurityAlert", "Paused", "Unpaused"):
            for event in getattr(contract.events, name).get_logs(from_block=EVENTS_FROM_BLOCK):
                args = dict(event["args"])
                items.append({
                    "event": name,
                    "block": event["blockNumber"],
                    "transactionHash": event["transactionHash"].hex(),
                    "account": args.get("user") or args.get("by"),
                    "action": args.get("action", ""),
                    "_order": (event["blockNumber"], event["logIndex"]),
                })
        items.sort(key=lambda item: item["_order"], reverse=True)
        for item in items:
            item.pop("_order", None)
        return jsonify(events=items[:100])
    except Exception as exc:
        app.logger.exception("Event retrieval failed")
        return jsonify(error=str(exc)), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
