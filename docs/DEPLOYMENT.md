# PORTLGuardLite — Deployment and Reproducibility Record

## 1. Deployment Environment

| Parameter | Recorded value |
|---|---|
| Network | Portaldot V3 Testnet |
| EVM Chain ID | `420420777` |
| Contract name | PORTLGuardLite |
| Solidity compiler compatibility | `^0.8.20` |

## 2. Deployment Evidence and Transaction Classification

| Deployment field | Current evidence |
|---|---|
| Contract address | `0x44406CD3e7ccE420c316D015FEE74303F16629E5` |
| Deployment block | `200580` |
| Deployment transaction hash | `0x6115a0880f1822ba7b43c5b0461323eaebab701f12ce22b81325a3d2b1e5d879` |
| Deployer | `0xde8547c35e4eb0cf3850a3f67def1defd4d43594` |
| Receipt status | Success (`0x1`) |

### Verified deployment evidence

The deployment transaction was independently checked through the Portaldot V3 RPC in Google Colab. Its successful receipt matches the contract address above and block `200580`. The transaction input begins with contract-creation bytecode (`0x60806040`), confirming that it is a contract creation transaction rather than a call to an existing contract.

The Portaldot Scanner independently shows the `revive(Instantiated)` event at block `200580`, with the deployed contract address matching:

`0x44406CD3e7ccE420c316D015FEE74303F16629E5`

### Separate protected-action interaction

Block `200641` is a later interaction with the deployed contract. The Scanner shows a `revive(ContractEmitted)` event for the same contract, corresponding to `protectedAction()` and the `Protected action executed` alert. This interaction is not the deployment transaction and remains part of the contract's on-chain activity history.

## 3. Contract Compilation

From the repository root, install the Python dependencies and compile the Solidity source:

```bash
pip install -r requirements.txt
python scripts/compile_contract.py
```

The compiler script reads `contracts/PORTLGuardLite.sol` and writes the ABI and bytecode artifact to `build/PORTLGuardLite.json`.

## 4. Existing Deployment Preservation

The PORTLGuardLite contract is already deployed at the address recorded above. Application organization, documentation changes and local compilation do not require another deployment. The deployment utility defaults to a local development RPC and includes a safety check for the Portaldot V3 Chain ID.

## 5. Local Development Deployment

For isolated development, start a local EVM node and configure its RPC endpoint in the local `.env` file. Then execute:

```bash
python scripts/deploy.py
```

Do not expose private keys in source code, repository files, logs or screenshots. Never commit `.env` or wallet credentials.
