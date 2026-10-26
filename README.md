# PORTLG — Smart Contract Security Guardrail

## Overview
PORTLG is a smart contract security demonstration built for the Portaldot V3 Testnet using Solidity and Remix IDE.

The project demonstrates how an owner can pause and resume protected smart contract operations while allowing multiple wallets to interact with the same deployed contract.

## Problem
Smart contracts need mechanisms to respond to security concerns and temporarily restrict sensitive operations.

## Our Solution
PORTLG demonstrates an owner-controlled emergency pause mechanism that can restrict protected actions without preventing users from connecting their wallets.

## Key Features
- **Pause:** The contract owner can temporarily disable protected operations.
- **Unpause:** The contract owner can restore protected operations.
- **Multi-Wallet Access:** Different wallets can call the protected function when the contract is active.
- **Owner Authorization:** Only the owner can pause or unpause the contract.
- **Security Events:** Contract events provide records of supported operations.

## How It Works
1. The owner deploys the smart contract.
2. A user connects a wallet to the Portaldot V3 Testnet.
3. The user calls `protectedAction()`.
4. The owner can activate `pause()` to block further protected actions.
5. The owner can call `unpause()` to restore access.

## Technology Stack
- Solidity
- Remix IDE
- MetaMask
- Portaldot V3 Testnet
- GitHub

## Blockchain Verification
Successful on-chain transactions can be checked using the Portaldot V3 Testnet Explorer:

https://scanner-testnet-v3.portaldot.dev/

Transaction hashes and deployment evidence will be added after verification.

## Current Status
The PORTLGuardLite contract has been deployed previously. Multi-wallet interaction and blockchain explorer verification are being tested.

## Future Improvements
- Security monitoring dashboard
- Additional access controls
- Automated security alerts
- Transaction activity visualization

## Disclaimer
PORTLG is an experimental testnet security demonstration. It has not undergone an independent security audit and should not be used to protect real funds.
