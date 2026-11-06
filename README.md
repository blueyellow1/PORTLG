# PORTLG Wallet

MetaMask-connected wallet interface and smart-contract security prototype on Portaldot V3 Testnet.

## Project structure

- `index.html`, `wallet.js` — GitHub Pages browser demonstration.
- `contracts/` — Solidity contract source.
- `frontend/` — frontend application source.
- `backend/` — Flask API source and dependencies.
- `scripts/` — compilation and deployment utilities.
- `tests/` — automated contract and backend tests.
- `docs/` — architecture, network, deployment, security, demo and test report.

## Network and deployed contract

- Network: Portaldot V3 Testnet
- Chain ID: `420420777`
- RPC: `https://test-evm-rpc-v3.portaldot.dev`
- Contract: `PORTLGuardLite`
- Address: `0x44406CD3e7ccE420c316D015FEE74303F16629E5`
- Deployment block: `200580`
- Deployment transaction: `0x6115a0880f1822ba7b43c5b0461323eaebab701f12ce22b81325a3d2b1e5d879`

## Documentation

- [Project file directory](docs/index.html)
- [Architecture](docs/ARCHITECTURE.md)
- [Network configuration](docs/NETWORK.md)
- [Deployment record](docs/DEPLOYMENT.md)
- [Security model and limitations](docs/SECURITY.md)
- [Demo procedure](docs/DEMO.md)
- [Automated test report](docs/TEST_REPORT.md)
- [Test instructions](tests/README.md)

## Development and tests

Install dependencies with `pip install -r requirements.txt`, then compile with `python scripts/compile_contract.py`. Run tests with `python -m unittest discover -s tests -p 'test_*.py' -v`. Tests use an isolated local EVM and do not modify the deployed Portaldot V3 contract.

GitHub Pages hosts the static browser demonstration only; it does not execute the Flask backend. MetaMask retains custody and signs transactions after user approval. The backend prepares unsigned transactions and does not hold private keys or seed phrases.

The contract supports owner-controlled `pause()` and `unpause()` and a `protectedAction()` that emits `SecurityAlert`. This event is not autonomous threat detection. The prototype has not undergone an independent security audit and must not be used to secure real funds. Native Assets, NFTs, guardians and multi-network support are outside the current scope.

- [Live demonstration](https://blueyellow1.github.io/PORTLG/)
- [GitHub repository](https://github.com/blueyellow1/PORTLG)
