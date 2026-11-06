# Backend — PORTLG Application and Transaction API

## Purpose
The Flask backend is an active application component. It serves the frontend, validates requested PORTLGuardLite operations against current on-chain state, prepares unsigned EVM transactions for MetaMask, and provides operational status and event history.

## End-to-end transaction workflow
1. The frontend sends the selected operation and connected wallet address to `POST /api/transactions/prepare`.
2. The backend validates the action, checks RPC connectivity, reads the contract owner and pause state, and rejects operations that are not currently allowed.
3. The backend returns an unsigned transaction request containing the contract destination and encoded function call.
4. The browser passes that request to MetaMask through the connected signer.
5. The user reviews and signs the transaction in MetaMask.
6. The frontend waits for the on-chain receipt, checks its success status, refreshes contract state and reloads contract events.

The backend never receives a seed phrase or private key, never signs for the user and never broadcasts a transaction on behalf of the wallet.

## API endpoints
| Method and path | Responsibility |
|---|---|
| `GET /` | Serves the PORTLG browser interface. |
| `GET /api/health` | Checks backend and RPC availability. |
| `GET /api/config` | Supplies the configured contract address and chain ID. |
| `GET /api/status` | Reads contract owner, pause state, network ID and current block. |
| `POST /api/transactions/prepare` | Validates a requested operation and returns unsigned transaction data for MetaMask. |
| `POST /api/transactions/confirm` | Verifies the submitted transaction, sender, destination, function and successful receipt on-chain. |
| `GET /api/events` | Retrieves `SecurityAlert`, `Paused` and `Unpaused` events from the configured deployment block. |

## Transaction preparation request
Example request body:

```json
{
  "action": "pause",
  "from": "0xYourConnectedMetaMaskAddress"
}
```

Supported actions: `pause`, `unpause`, `protectedAction`.

The backend rejects unsupported actions, invalid wallet addresses, non-owner pause/resume requests, attempts to pause an already paused contract, attempts to resume an active contract and protected actions while paused. The smart contract remains the final authority: its on-chain access-control rules cannot be bypassed by a backend response.

## Configuration
The service reads `.env` from the repository root. Configure `RPC_URL`, `CHAIN_ID`, `CONTRACT_ADDRESS` and `EVENTS_FROM_BLOCK` using `.env.example`. Never commit credentials.

## Run
From the repository root:

```bash
pip install -r requirements.txt
python scripts/compile_contract.py
python backend/app.py
```

Open `http://127.0.0.1:5000`. The browser frontend and API are served from the same origin.

## Trust and security boundaries
- MetaMask controls account access and transaction signing.
- The backend prepares unsigned transaction data; it does not custody wallet keys.
- The address supplied to the preparation endpoint is a client assertion, not proof of identity. The contract's `onlyOwner` modifier independently enforces owner authorization on-chain.
- Backend pre-validation improves usability but cannot replace smart-contract enforcement.
- The service is a testnet prototype and should be deployed behind HTTPS with production-grade rate limiting, monitoring and operational controls before public use.

## Verification
Use the UI to connect MetaMask, request each supported operation and verify the transaction receipt and corresponding state/event changes on Portaldot V3. RPC or API failures must be treated as errors, not successful operations.
