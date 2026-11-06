# PORTLG Wallet — System Architecture

## 1. Architecture Overview

PORTLG is composed of a browser-based wallet interface, a Flask application backend, MetaMask as the user-controlled signer, the Portaldot V3 EVM network and the PORTLGuardLite smart contract.

```text
User
 |
 v
PORTLG Frontend (HTML / CSS / JavaScript)
 |                         |
 | API requests            | Wallet signing request
 v                         v
Flask Backend           MetaMask
 |                         |
 | validates and            | signs after user approval
 | prepares unsigned tx     |
 |                         |
 +-------------------------+
             |
             v
      Portaldot V3 EVM RPC
             |
             v
        PORTLGuardLite
             |
             v
     On-chain state and events
```

## 2. Application Components

### Browser Frontend
The frontend connects to MetaMask, verifies the selected chain, displays wallet and contract state, submits action requests to the backend, asks MetaMask to sign prepared transactions and waits for transaction receipts.

### Flask Backend
The backend serves the frontend and provides application endpoints. It validates requested contract actions against the current owner and pause state, creates unsigned transaction calldata, reports backend/RPC health and retrieves contract events. It does not hold wallet keys or sign transactions.

### MetaMask
MetaMask provides account access and signs each transaction only after the user approves it. The frontend sends the unsigned transaction request returned by the backend to the connected MetaMask signer.

### Portaldot V3 EVM Network
The EVM RPC provides access to contract state, transaction submission, receipts and emitted logs.

### PORTLGuardLite
The Solidity contract enforces owner-only emergency controls and prevents its protected action from running while paused.

## 3. Backend-to-Frontend API Contract

| Endpoint | Frontend use |
|---|---|
| `GET /api/health` | Check backend and RPC readiness |
| `GET /api/config` | Load contract address and required chain ID |
| `GET /api/status` | Display current contract owner, pause state and block |
| `POST /api/transactions/prepare` | Request validation and unsigned transaction calldata |
| `GET /api/events` | Display on-chain event history |

## 4. Transaction Lifecycle

1. The user connects MetaMask to the PORTLG interface.
2. The frontend verifies the Portaldot V3 chain ID and loads backend configuration.
3. The user selects Pause, Unpause or Protected Action.
4. The frontend submits the action and connected account address to the backend.
5. The backend checks RPC availability, contract state, requested operation and owner restrictions.
6. The backend returns unsigned transaction data.
7. The frontend passes the transaction to MetaMask.
8. The user reviews and approves the transaction.
9. MetaMask signs and submits it to Portaldot V3.
10. The frontend waits for the receipt and refreshes state and events.

## 5. Contract Interface

| Function / Event | Purpose |
|---|---|
| `owner()` | Returns the contract owner address |
| `paused()` | Returns the current emergency pause state |
| `pause()` | Sets the contract to paused; owner only |
| `unpause()` | Resumes contract operation; owner only |
| `protectedAction()` | Executes only while the contract is not paused |
| `SecurityAlert` | Records invocation of the protected action |
| `Paused` | Records an emergency pause |
| `Unpaused` | Records resumption |

## 6. Security and Trust Boundaries

The backend's owner check is a pre-validation step based on the wallet address supplied by the browser. It is not cryptographic proof of account ownership. MetaMask signs the transaction, and the deployed smart contract independently enforces `onlyOwner`; therefore, a forged API request cannot bypass the contract's access control.

The backend never receives private keys or seed phrases. It prepares transactions but does not sign or broadcast them for the user. The contract emits an event when the protected operation is invoked; it does not independently detect malicious behavior or automatically pause itself.

## 7. Current Implementation Boundary

PORTLG is a MetaMask-connected wallet interface prototype integrated with a contract-control backend. It is not an independent key-custody wallet. Its current supported contract operations are Pause, Unpause and Protected Action on Portaldot V3 Testnet.
