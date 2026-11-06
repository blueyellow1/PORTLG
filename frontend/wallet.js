"use strict";

const REQUIRED_CHAIN_ID = 420420777n;
const CONTRACT_ABI = [
  "function owner() view returns (address)",
  "function paused() view returns (bool)"
];

let provider;
let signer;
let readContract;
let connectedAccount;
let backendConfig;

const element = (id) => document.getElementById(id);
const setStatus = (message) => { element("txStatus").textContent = message; };

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || `Backend request failed (${response.status}).`);
  return result;
}

async function refreshContractState() {
  const [owner, paused, backendStatus] = await Promise.all([
    readContract.owner(),
    readContract.paused(),
    api("/api/status")
  ]);

  element("contractStatus").textContent = paused ? "Paused" : "Active";
  element("ownerAddress").textContent = `Owner: ${owner}`;
  element("backendStatus").textContent =
    backendStatus.connected ? `Backend connected · block ${backendStatus.block}` : "Backend unavailable";

  const isOwner = connectedAccount.toLowerCase() === owner.toLowerCase();
  element("pauseBtn").disabled = !isOwner || paused;
  element("unpauseBtn").disabled = !isOwner || !paused;
  element("actionBtn").disabled = paused;
}

async function connectWallet() {
  try {
    if (!window.ethereum) throw new Error("MetaMask is not available. Install or unlock MetaMask.");

    provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []);

    const network = await provider.getNetwork();
    if (network.chainId !== REQUIRED_CHAIN_ID) {
      throw new Error("Please select Portaldot V3 Testnet in MetaMask.");
    }

    signer = await provider.getSigner();
    connectedAccount = await signer.getAddress();
    backendConfig = await api("/api/config");

    if (Number(backendConfig.chainId) !== Number(network.chainId)) {
      throw new Error("The backend and MetaMask network configurations do not match.");
    }

    const bytecode = await provider.getCode(backendConfig.address);
    if (bytecode === "0x") throw new Error("PORTLGuardLite bytecode was not found at the configured address.");

    readContract = new ethers.Contract(backendConfig.address, CONTRACT_ABI, provider);
    element("walletAddress").textContent = connectedAccount;
    await refreshContractState();
    setStatus("Wallet and backend connected. Contract controls are ready.");
    await loadEvents();
  } catch (error) {
    setStatus(error.shortMessage || error.message);
  }
}

async function submitContractTransaction(action) {
  try {
    if (!signer || !connectedAccount) throw new Error("Connect MetaMask before submitting a transaction.");

    setStatus("Validating operation with PORTLG backend...");
    const prepared = await api("/api/transactions/prepare", {
      method: "POST",
      body: JSON.stringify({ action, from: connectedAccount })
    });

    setStatus("Transaction prepared. Waiting for your MetaMask approval...");
    const transaction = await signer.sendTransaction(prepared.transaction);
    setStatus(`Submitted: ${transaction.hash}`);

    const receipt = await transaction.wait();
    if (!receipt || receipt.status !== 1) throw new Error("The blockchain did not confirm this transaction successfully.");

    setStatus("Receipt detected. Verifying transaction with PORTLG backend...");
    const verification = await api("/api/transactions/confirm", {
      method: "POST",
      body: JSON.stringify({
        transactionHash: transaction.hash,
        action,
        from: connectedAccount
      })
    });
    setStatus(`Backend verified ${verification.action} · Block ${verification.blockNumber} · Tx: ${verification.transactionHash}`);
    await refreshContractState();
    await loadEvents();
  } catch (error) {
    setStatus(error.shortMessage || error.message);
  }
}

async function loadEvents() {
  try {
    const result = await api("/api/events");
    const list = element("eventList");
    list.replaceChildren();
    if (!result.events.length) {
      list.textContent = "No contract events found from the configured deployment block.";
      return;
    }
    for (const item of result.events) {
      const row = document.createElement("p");
      row.textContent = `${item.event} · Block ${item.block} · ${item.account || "—"} · ${item.transactionHash}`;
      list.appendChild(row);
    }
  } catch (error) {
    element("eventList").textContent = `Event service unavailable: ${error.message}`;
  }
}

element("connectBtn").addEventListener("click", connectWallet);
element("pauseBtn").addEventListener("click", () => submitContractTransaction("pause"));
element("unpauseBtn").addEventListener("click", () => submitContractTransaction("unpause"));
element("actionBtn").addEventListener("click", () => submitContractTransaction("protectedAction"));

if (window.ethereum) {
  window.ethereum.on("accountsChanged", () => window.location.reload());
  window.ethereum.on("chainChanged", () => window.location.reload());
}
