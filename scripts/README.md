# Build and Deployment Scripts

## Purpose
This directory contains repeatable developer scripts for compiling PORTLGuardLite and, when deliberately required, deploying a new instance to a development network.

## compile_contract.py
- Reads `contracts/PORTLGuardLite.sol`.
- Uses py-solc-x with Solidity `0.8.24`.
- Writes the ABI and bytecode artifact to `build/PORTLGuardLite.json`.

Run from the repository root:
```bash
python scripts/compile_contract.py
```

## deploy.py
The deployment script is intended for local development. It refuses to deploy to Portaldot V3 Testnet unless `ALLOW_TESTNET_DEPLOYMENT=true` is explicitly set. The existing PORTLG deployment should not be redeployed as part of routine documentation or frontend work.

Run only against a deliberately selected development RPC:
```bash
python scripts/deploy.py
```

## Environment
Configuration is read from the root `.env` file. Start from `.env.example`. The backend read RPC is configured with `RPC_URL`; the deployment utility uses the separate `DEPLOY_RPC_URL` setting and defaults to a local node. Keep private keys out of source control.

## Evidence
A successful compile should produce the artifact file. A successful deployment must produce a transaction hash, a successful receipt, a contract address and a block number. Do not report a deployment or test as successful without retaining its actual output.
