# PORTLG Wallet
### MetaMask-connected wallet interface and smart-contract security on Portaldot V3 Testnet

## Project overview
PORTLG is a browser-based wallet interface prototype connected to MetaMask and the PORTLGuardLite smart contract. The current deployed contract provides owner-controlled emergency pause and resume operations, a protected action, and on-chain event records.

The project repository separates the browser interface, backend API, Solidity contract, development scripts, automated tests and technical documentation into dedicated directories.

## Implemented scope
- MetaMask account connection and Portaldot V3 Testnet chain verification.
- PORTLGuardLite contract-state reads.
- Owner-restricted `pause()` and `unpause()`.
- `protectedAction()`, which is unavailable while the contract is paused.
- On-chain `SecurityAlert`, `Paused` and `Unpaused` events.
- Flask API source for operation validation, unsigned transaction preparation, receipt verification and event retrieval.

The browser-hosted GitHub Pages demonstration is a static site. GitHub Pages does not execute the Flask backend; backend API workflows require a Python runtime as described in the backend documentation.

## Network and existing deployment
| Parameter | Value |
|---|---|
| Network | Portaldot V3 Testnet |
| Chain ID | `420420777` |
| EVM RPC | `https://test-evm-rpc-v3.portaldot.dev` |
| Contract | `PORTLGuardLite` |
| Contract address | `0x44406CD3e7ccE420c316D015FEE74303F16629E5` |
| Deployment block | `200580` |
| Deployment transaction | `0x6115a0880f1822ba7b43c5b0461323eaebab701f12ce22b81325a3d2b1e5d879` |

## Repository structure
```text
PORTLG/
├── index.html
├── wallet.js
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── .github/
│   └── workflows/
│       └── contract-tests.yml
├── contracts/
│   ├── PORTLGuardLite.sol
│   └── README.md
├── frontend/
│   ├── index.html
│   ├── wallet.js
│   └── README.md
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
├── scripts/
│   ├── compile_contract.py
│   ├── deploy.py
│   └── README.md
├── tests/
│   ├── test_portlguardlite.py
│   ├── test_backend_api.py
│   └── README.md
└── docs/
    ├── index.html
    ├── ARCHITECTURE.md
    ├── NETWORK.md
    ├── DEPLOYMENT.md
    ├── SECURITY.md
    ├── DEMO.md
    ├── PORTALDOT_GUIDE_MAPPING.md
    └── README.md
```

## Technical documentation
- [Project file directory](docs/)
- [System architecture](docs/ARCHITECTURE.md)
- [Network configuration](docs/NETWORK.md)
- [Deployment record](docs/DEPLOYMENT.md)
- [Security model and limitations](docs/SECURITY.md)
- [Demonstration procedure](docs/DEMO.md)
- [Portaldot V3 guide mapping](docs/PORTALDOT_GUIDE_MAPPING.md)
- [Automated test documentation](tests/README.md)

## Local development
From the repository root:
```bash
pip install -r requirements.txt
cp .env.example .env
python scripts/compile_contract.py
python backend/app.py
```
Open `http://127.0.0.1:5000` and connect MetaMask to Portaldot V3 Testnet.

## Tests
```bash
python scripts/compile_contract.py
python -m unittest discover -s tests -p 'test_*.py' -v
```
These tests use an isolated local EVM and do not modify the existing Portaldot V3 deployment.

## Security boundaries and limitations
MetaMask retains custody of the account and signs transactions after user approval. The backend prepares unsigned transactions; the contract independently enforces owner-only access. The contract's `SecurityAlert` event records protected-action execution; it is not autonomous threat detection. This prototype has not undergone an independent security audit and must not be used to secure real funds.

Native Assets, NFTs, guardians and multi-network support are outside the current implementation scope.

## Links
- [PORTLG Wallet website](https://blueyellow1.github.io/PORTLG/)
- [GitHub repository](https://github.com/blueyellow1/PORTLG)
