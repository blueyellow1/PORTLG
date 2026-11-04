# PORTLG Wallet — Development Record

## Project Development
PORTLG evolved from a smart-contract security demonstration into a browser-based wallet interface integrated with PORTLGuardLite.

## Current Implementation
- MetaMask wallet connection
- Portaldot V3 Testnet network connection
- Native tPOT balance display
- Native tPOT transfer interface
- Recipient address validation
- Amount and balance validation
- Local transaction history
- Blockchain explorer links
- PORTLGuardLite emergency pause and unpause controls

## Smart Contract
- Contract: PORTLGuardLite
- Address: 0x44406CD3e7ccE420c316D015FEE74303F16629E5
- Owner-controlled pause and unpause
- Protected action
- SecurityAlert, Paused and Unpaused events

## Development Technology
- Solidity
- HTML and CSS
- JavaScript
- ethers.js
- MetaMask
- Portaldot V3 Testnet
- GitHub and GitHub Pages

## Network Configuration
- Network: Portaldot V3 Testnet
- Chain ID: 420420777
- Native token: tPOT
- RPC: https://test-evm-rpc-v3.portaldot.dev
- Explorer: https://scanner-testnet-v3.portaldot.dev/

## Current Limitations
- MetaMask provides account access and transaction signing.
- The current implementation targets Portaldot V3 Testnet.
- Transaction history is stored locally in the browser.
- Automatic threat detection and guardian-based security are not implemented.
- The project has not undergone an independent security audit.

## Future Development
- Multi-network wallet support
- Improved transaction monitoring
- Automated security risk detection
- Guardian-based security mechanisms

## Development Status
The browser wallet interface and PORTLGuardLite integration are under active development. Further testing and security review are required.

## Project Repository
https://github.com/blueyellow1/PORTLG

## Live Website
https://blueyellow1.github.io/PORTLG/
