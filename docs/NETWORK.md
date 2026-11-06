# Portaldot V3 Testnet — Network Configuration

PORTLG is configured to interact with the Portaldot V3 EVM-compatible test network.

## Network Parameters

| Parameter | Configuration |
|---|---|
| Network name | Portaldot V3 Testnet |
| EVM RPC endpoint | `https://test-evm-rpc-v3.portaldot.dev` |
| Substrate WebSocket endpoint | `wss://test-node-v3.portaldot.dev` |
| EVM Chain ID | `420420777` |
| Native token symbol | `tPOTv3` |
| Native token precision | `14` decimals |
| Node Explorer | `https://node-console.portaldot.dev` |

## MetaMask Configuration

Add Portaldot V3 Testnet as a custom network in MetaMask using the EVM RPC endpoint, Chain ID and native token symbol listed above. The application checks the active chain ID before enabling contract interaction.

## RPC Usage

The EVM JSON-RPC endpoint is used for:
- Retrieving deployed contract bytecode.
- Reading contract state, including `owner()` and `paused()`.
- Submitting signed contract transactions through the wallet provider.
- Waiting for transaction receipts.

The Substrate WebSocket endpoint is documented as the network's native WebSocket interface; the current PORTLG EVM frontend uses the EVM RPC through MetaMask.

## Network Compatibility

The current frontend targets Portaldot V3 Testnet and validates Chain ID `420420777`. The native token precision is documented as 14 decimals in the Portaldot V3 guide. PORTLG's current interface does not expose a native-token transfer form, so no transfer precision is assumed by its transaction controls.

Use the current V3 endpoints rather than legacy network endpoints. Consult the [Portaldot V3 Testnet Guide](https://github.com/ItsCogumellum/portaldot-v3-testnet-guide) for network-specific technical references.
