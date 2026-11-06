# PORTLG — Technical Demonstration Procedure

## Demonstration Objective
Demonstrate a complete application workflow across the PORTLG frontend, Flask backend, MetaMask and the deployed PORTLGuardLite contract on Portaldot V3 Testnet.

## Environment Preparation
1. Install the project dependencies and compile the contract ABI.
2. Start the Flask application from the repository root using `python backend/app.py`.
3. Open `http://127.0.0.1:5000` (do not open the HTML file directly).
4. Select Portaldot V3 Testnet in MetaMask (Chain ID: `420420777`).
5. Connect the wallet through the PORTLG interface.
6. Confirm the interface reports backend connectivity and displays the contract owner and pause state.

## Complete Transaction Sequence

### A. Wallet and Backend Connectivity
Show the connected MetaMask account, selected network and backend connection status.

### B. Backend Transaction Preparation
Select an available operation. Show the frontend sending the operation and connected account to the backend. The backend validates the requested action against the contract's current state and returns unsigned transaction data.

### C. User Authorization and Blockchain Execution
Show MetaMask presenting the transaction for approval. Approve it with the intended account. PORTLG waits for the transaction receipt.

### D. Backend Receipt Verification
Show the frontend submitting the transaction hash to the backend confirmation endpoint. The backend verifies the destination contract, sender, function selector and successful on-chain receipt.

### E. Protected Operation
When the contract is active, submit `protectedAction()`. Confirm the successful receipt and `SecurityAlert` event.

### F. Emergency Pause and Resume
Using the owner account, submit `pause()` and verify the paused state. Confirm that a protected action is rejected while paused. Then submit `unpause()` using the owner account and verify the active state.

## Evidence to Capture
- Connected wallet address and selected chain.
- Backend health and contract status.
- Backend-prepared transaction request (without secrets).
- MetaMask transaction approval.
- Transaction hash, successful receipt and block number.
- Backend transaction verification response.
- Contract state transition and emitted event records.

Only report transactions and event records confirmed on-chain. The backend does not sign transactions or hold wallet keys; MetaMask approval remains mandatory.
