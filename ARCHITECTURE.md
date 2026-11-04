
# PORTLG Wallet Architecture

## Overview
PORTLG is a browser-based wallet interface connected to MetaMask and Portaldot V3 Testnet. It also includes the PORTLGuardLite smart contract.

## Architecture

User
  |
  v
PORTLG Wallet (HTML, CSS, JavaScript)
  |
  v
wallet.js
  |
  v
MetaMask
  |
  v
Portaldot V3 RPC
  |
  v
Portaldot V3 Testnet
  |
  +-- Token Balance
  +-- Transaction Processing
  +-- Blockchain Explorer

PORTLG Security Interface
  |
  v
PORTLGuardLite Smart Contract
  |
  +-- Pause / Unpause
  +-- SecurityAlert Events

## Main Components
- Wallet interface: User interaction.
- wallet.js: Wallet connection, address validation and transaction submission.
- MetaMask: Account access and transaction signing.
- Portaldot RPC: Blockchain communication.
- Explorer: Transaction verification.
- Local Storage: Browser transaction history.
- PORTLGuardLite: Pause/unpause and security events.

## Network
- Network: Portaldot V3 Testnet
- Chain ID: 420420777
- RPC: https://test-evm-rpc-v3.portaldot.dev
- Contract: 0x44406CD3e7ccE420c316D015FEE74303F16629E5

## Security
- MetaMask transaction authorization.
- Recipient address validation.
- Amount validation.
- Network verification.
- Balance verification.
- Owner-controlled pause and unpause.
- SecurityAlert event emission.

## Current Limitations
The wallet currently relies on MetaMask for account access and signing. It does not independently generate or store private keys. Transaction history is stored locally in the browser. Multi-network support, automatic threat detection and guardian-based security are future goals.

## Technology
Solidity ^0.8.20, HTML, CSS, JavaScript, ethers.js, MetaMask and Portaldot V3 Testnet.
