"""Deploy PORTLGuardLite for local development only.

Run from repository root: python scripts/deploy.py
Live Portaldot deployment is blocked unless explicitly enabled.
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main():
    artifact = ROOT / "build" / "PORTLGuardLite.json"
    if not artifact.exists():
        sys.exit("Run python scripts/compile_contract.py first.")

    rpc = os.getenv("DEPLOY_RPC_URL", "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        sys.exit(f"Cannot connect to {rpc}; start a local development node.")

    if w3.eth.chain_id == 420420777 and os.getenv("ALLOW_TESTNET_DEPLOYMENT") != "true":
        sys.exit("Safety stop: Portaldot V3 deployment is disabled. Set ALLOW_TESTNET_DEPLOYMENT=true only if you deliberately intend a new deployment.")

    build = json.loads(artifact.read_text())
    contract = w3.eth.contract(abi=build["abi"], bytecode=build["bytecode"])
    key = os.getenv("PRIVATE_KEY")
    if key:
        account = w3.eth.account.from_key(key)
        tx = contract.constructor().build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    else:
        if not w3.eth.accounts:
            sys.exit("No unlocked local development account is available.")
        tx_hash = contract.constructor().transact({"from": w3.eth.accounts[0]})

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Deployed at", receipt.contractAddress)
    print("Transaction:", tx_hash.hex())
    print("Block:", receipt.blockNumber)


if __name__ == "__main__":
    main()
