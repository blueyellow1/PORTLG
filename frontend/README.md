# Frontend — PORTLG Wallet

## Purpose
This directory contains the browser wallet interface. It communicates with the Flask backend for application configuration, operation validation, unsigned transaction preparation, receipt verification and contract event history. MetaMask remains the user's transaction signer.

## Components
- `index.html`: wallet panels, contract controls, backend status, event history and transaction feedback.
- `wallet.js`: MetaMask connection, chain verification, backend API requests, transaction signing request and confirmation display.
- ethers.js v6 is loaded by the HTML page from a public CDN.

## Implemented user workflow
1. Connect MetaMask and verify Portaldot V3 Testnet (Chain ID `420420777`).
2. Load the configured contract address and verify that contract bytecode exists.
3. Read contract state and backend/RPC status.
4. Select Pause, Unpause or Protected Action.
5. Send the requested action and connected account to `POST /api/transactions/prepare`.
6. Receive unsigned transaction data from the backend and submit it to MetaMask for user approval.
7. Wait for the blockchain receipt.
8. Ask `POST /api/transactions/confirm` to verify the transaction destination, sender, function and successful receipt.
9. Refresh contract state and event history from the backend.

## Run
From the repository root:

```bash
pip install -r requirements.txt
python scripts/compile_contract.py
python backend/app.py
```

Open `http://127.0.0.1:5000`. The frontend and backend share the same origin; do not open `index.html` directly from the filesystem.

## Security notes
MetaMask retains control of the account and signs transactions. The frontend does not request, read or store seed phrases or private keys. Backend pre-validation is not a substitute for on-chain authorization; PORTLGuardLite independently enforces owner-only functions.

## Verification
Follow [../docs/DEMO.md](../docs/DEMO.md). A successful API response is not enough by itself: verify the transaction hash, successful receipt and expected state/event change on Portaldot V3.
