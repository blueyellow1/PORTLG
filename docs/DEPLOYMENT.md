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
| Deployment block | `200641` (block identified in reviewer feedback; exact creation extrinsic still needs matching) |
| Deployment transaction hash | **Not yet confirmed** |

### Correction to the previously listed transaction

The previously recorded hash

`0x6115a0880f1822ba7b43c5b0461323eaebab701f12ce22b81325a3d2b1e5d879`

must not be used as the deployment transaction. The reviewer identified its four-byte input selector, `0x3d7b369a`, as `protectedAction()`. This makes it a call to an already deployed contract, not the transaction that created the contract.

The reviewer also confirmed that the contract code exists at the address above and referenced block `200641`. The exact contract-creation transaction hash has not yet been matched to a creation extrinsic and its `Instantiated` event. Therefore, this document deliberately leaves the deployment hash unconfirmed rather than substituting a contract-interaction hash or guessing another hash.

### What qualifies as deployment evidence

The correct deployment record must point to the contract-creation extrinsic and its execution event, with the emitted contract address matching:

`0x44406CD3e7ccE420c316D015FEE74303F16629E5`

A `Contracts.call` / `protectedAction()` transaction is an interaction after deployment and belongs in interaction or test evidence, not in the deployment field.

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
