# PORTLG — Security Model

## 1. Security Design

PORTLG demonstrates contract-enforced access control and an emergency pause mechanism integrated with a browser wallet interface.

The security model is based on three principles:

- **User authorization:** MetaMask requires the account holder to approve transactions.
- **Role restriction:** PORTLGuardLite limits emergency pause and resume operations to the contract owner.
- **State enforcement:** the smart contract rejects the protected operation while its paused state is active.

## 2. Contract-Level Controls

| Control | Enforcement |
|---|---|
| `pause()` | Restricted by the `onlyOwner` modifier |
| `unpause()` | Restricted by the `onlyOwner` modifier |
| `protectedAction()` | Restricted by the `whenNotPaused` modifier |
| `Paused` event | Emitted when the contract enters paused state |
| `Unpaused` event | Emitted when the contract resumes |
| `SecurityAlert` event | Emitted when the protected action executes |

These restrictions are enforced by the deployed contract and remain effective independently of frontend presentation.

## 3. Wallet Authorization

MetaMask provides account access and transaction signing. PORTLG does not request, transmit or store the user's seed phrase or private key. Each contract transaction requires wallet-provider authorization.

## 4. Event-Based Audit Trail

The contract emits events for pause, resume and protected-action execution. These events provide on-chain records that can be inspected using compatible blockchain tooling.

The `SecurityAlert` event records execution of the protected operation. It does not represent automated anomaly detection, malicious-address classification or autonomous incident response.

## 5. Security Scope

PORTLGuardLite is a focused demonstration contract. No independent third-party security audit is claimed. The application is intended for testnet development and evaluation; it should not be used to secure real funds or production assets.
