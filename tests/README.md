# Verification and Test Evidence

## Purpose
This directory contains executable local EVM contract tests, Flask backend API tests and guidance for recording test evidence.

## Automated contract tests
`test_portlguardlite.py` deploys the compiled contract to an isolated in-memory Ethereum test chain. It checks:
- Deployer ownership and the initial active state.
- Owner-only pause authorization.
- Owner-only resume authorization.
- Successful protected-action execution and `SecurityAlert` event emission.
- Rejection of the protected action while paused.

- `test_backend_api.py` validates backend request validation, unsigned transaction preparation, owner-only pre-validation and paused-state rejection using a mocked RPC boundary. It does not submit live transactions.\n\n## Run the tests
From the repository root:

```bash
pip install -r requirements.txt
python scripts/compile_contract.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

The tests use a local ephemeral test chain. They do not send transactions to Portaldot V3 and do not modify the existing deployed contract.

## Additional integration verification
| Area | Verification evidence |
|---|---|
| Deployment record | Contract address, deployment transaction, block and successful receipt independently checked against the network. |
| Frontend connection | MetaMask account and required chain are detected correctly. |
| End-to-end interaction | UI transaction is signed, confirmed on-chain and reflected in refreshed contract state. |
| Backend API | Status and event endpoints return expected data against the configured RPC. |

## Evidence policy
Record the command, environment, timestamp, result and relevant transaction hash or test report for each executed test. Mark each check as PASS, FAIL or NOT RUN. Do not mark a test as PASS based only on source-code inspection.

Automated test cases are provided, but no test result is claimed until the commands above have actually been executed and their output reviewed.
