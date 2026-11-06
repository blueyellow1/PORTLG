# Smart Contract — PORTLGuardLite

## Purpose
This directory contains the Solidity source code for PORTLG's on-chain emergency control demonstration.

## Contract
`PORTLGuardLite.sol` implements:
- `owner`: the deployer address recorded during construction.
- `paused`: current emergency pause state.
- `pause()`: owner-only transition to the paused state.
- `unpause()`: owner-only transition back to the active state.
- `protectedAction()`: callable only while the contract is active.
- `Paused`, `Unpaused` and `SecurityAlert` events for on-chain activity records.

## Access-control behavior
Calls to `pause()` and `unpause()` from any address other than `owner` revert with `Not authorized`. The protected action reverts while paused. The contract does not autonomously detect malicious activity; the alert event records execution of the protected action.

## Compiler
Solidity pragma: `^0.8.20`. The repository compilation script currently selects Solidity compiler `0.8.24`.

## Existing deployment record
Portaldot V3 Testnet contract: `0x44406CD3e7ccE420c316D015FEE74303F16629E5`.
Deployment block: `200580`.
Deployment transaction: `0x6115a0880f1822ba7b43c5b0461323eaebab701f12ce22b81325a3d2b1e5d879`.

The source is included for reproducibility and review. Recompiling the source does not itself prove bytecode equivalence with the deployed instance; verify compiler settings and deployed bytecode before making that claim.

## Compile
From the repository root: `python scripts/compile_contract.py`.
See [../scripts/README.md](../scripts/README.md) for the build workflow.
