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
let paidAccessToken = null;
let paidAccessAccount = null;

const element = (id) => document.getElementById(id);
const setStatus = (message) => { element("txStatus").textContent = message; };

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(paidAccessToken ? { Authorization: `Bearer ${paidAccessToken}` } : {}),
    ...(options.headers || {})
  };
  const response = await fetch(path, { ...options, headers });
  const result = await response.json().catch(() => ({}));
  if (!response.ok && response.status !== 202) throw new Error(result.error || `Backend request failed (${response.status}).`);
  return result;
}

function updatePaidAccessControls() {
  const allowed = Boolean(paidAccessAccount && paidAccessAccount.accessAllowed);
  element("actionBtn").disabled = !allowed || !readContract;
}

async function refreshPaidAccess() {
  if (!paidAccessToken) {
    paidAccessAccount = null;
    element("paidAccessStatus").textContent = "Not signed in. Sign in with MetaMask to start or view your trial.";
    element("recoverBtn").disabled = !signer;
    updatePaidAccessControls();
    return;
  }
  try {
    const result = await api("/api/paid-access/status");
    paidAccessAccount = result.account;
    const account = paidAccessAccount;
    const trialText = account.trialActive ? "Trial active" : "Trial expired";
    const lockText = account.locked ? " · Account temporarily locked" : "";
    element("paidAccessStatus").textContent =
      `${trialText} · ${account.creditsRemaining} credits remaining${lockText}`;
    element("recoverBtn").disabled = !account.locked;
  } catch (error) {
    paidAccessToken = null;
    paidAccessAccount = null;
    element("paidAccessStatus").textContent = `Paid Access session unavailable: ${error.message}`;
    element("recoverBtn").disabled = !signer;
  }
  updatePaidAccessControls();
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
  updatePaidAccessControls();
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
    element("signInBtn").disabled = false;
    await refreshPaidAccess();
    await refreshContractState();
    setStatus("Wallet and backend connected. Sign in to enable Protected Action.");
    await loadEvents();
  } catch (error) {
    setStatus(error.shortMessage || error.message);
  }
}

async function signInPaidAccess() {
  try {
    if (!signer || !connectedAccount) throw new Error("Connect MetaMask first.");
    element("signInBtn").disabled = true;
    element("paidAccessStatus").textContent = "Requesting a one-time sign-in message...";
    const challenge = await api("/api/paid-access/challenge", {
      method: "POST",
      body: JSON.stringify({ wallet: connectedAccount })
    });
    const signature = await signer.signMessage(challenge.message);
    const result = await api("/api/paid-access/verify", {
      method: "POST",
      body: JSON.stringify({
        wallet: connectedAccount,
        nonce: challenge.nonce,
        signature
      })
    });
    paidAccessToken = result.token;
    paidAccessAccount = result.account;
    await refreshPaidAccess();
    await refreshContractState();
    element("paidAccessStatus").textContent =
      `Signed in · ${paidAccessAccount.trialActive ? "Trial active" : "Trial expired"} · ${paidAccessAccount.creditsRemaining} credits remaining`;
  } catch (error) {
    element("paidAccessStatus").textContent = error.message;
  } finally {
    element("signInBtn").disabled = !signer;
  }
}

async function recoverPaidAccess() {
  try {
    if (!signer || !connectedAccount) throw new Error("Connect the locked wallet first.");
    element("recoverBtn").disabled = true;
    const challenge = await api("/api/paid-access/recovery/challenge", {
      method: "POST",
      body: JSON.stringify({ wallet: connectedAccount })
    });
    const signature = await signer.signMessage(challenge.message);
    const result = await api("/api/paid-access/recovery/verify", {
      method: "POST",
      body: JSON.stringify({
        wallet: connectedAccount,
        nonce: challenge.nonce,
        signature
      })
    });
    paidAccessAccount = result.account;
    element("paidAccessStatus").textContent =
      `Account recovered · ${paidAccessAccount.creditsRemaining} credits remaining. Sign in again to continue.`;
    paidAccessToken = null;
    await refreshPaidAccess();
  } catch (error) {
    element("paidAccessStatus").textContent = error.message;
    element("recoverBtn").disabled = false;
  }
}

async function submitContractTransaction(action) {
  try {
    if (!signer || !connectedAccount) throw new Error("Connect MetaMask before submitting a transaction.");
    if (action === "protectedAction" && (!paidAccessAccount || !paidAccessAccount.accessAllowed)) {
      throw new Error("Sign in with an active Paid Access trial and available credits first.");
    }

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
    let verification;
    for (let attempt = 0; attempt < 30; attempt += 1) {
      verification = await api("/api/transactions/confirm", {
        method: "POST",
        body: JSON.stringify({
          transactionHash: transaction.hash,
          action,
          from: connectedAccount
        })
      });
      if (verification.confirmed) break;
      if (verification.status !== "pending") {
        throw new Error(verification.error || "The backend could not confirm this transaction.");
      }
      setStatus(`Waiting for required confirmations: ${verification.confirmations}/${verification.requiredConfirmations}`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    if (!verification || !verification.confirmed) {
      throw new Error("The transaction is still awaiting backend confirmation. Refresh status before retrying.");
    }

    setStatus(`Backend verified ${verification.action} · Block ${verification.blockNumber} · Tx: ${verification.transactionHash}`);
    await refreshPaidAccess();
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
element("signInBtn").addEventListener("click", signInPaidAccess);
element("recoverBtn").addEventListener("click", recoverPaidAccess);
element("pauseBtn").addEventListener("click", () => submitContractTransaction("pause"));
element("unpauseBtn").addEventListener("click", () => submitContractTransaction("unpause"));
element("actionBtn").addEventListener("click", () => submitContractTransaction("protectedAction"));

if (window.ethereum) {
  window.ethereum.on("accountsChanged", () => window.location.reload());
  window.ethereum.on("chainChanged", () => window.location.reload());
}
