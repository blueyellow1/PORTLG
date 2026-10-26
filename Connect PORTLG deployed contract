
const CONTRACT_ADDRESS = "0x44406CD3e7ccE420c316D015FEE74303F16629E5";
// Weka address ya PORTLGuardLite iliyothibitishwa hapa.

const CHAIN_ID = 420420777n;
const EXPLORER = "https://scanner-testnet-v3.portaldot.dev";

const ABI = [
  "function owner() view returns (address)",
  "function paused() view returns (bool)",
  "function pause()",
  "function unpause()",
  "function protectedAction()"
];

let provider;
let signer;
let contract;
let wallet;

const $ = (id) => document.getElementById(id);

function showStatus(message) {
  $("txStatus").textContent = message;
}

function updateButtons(owner, isPaused) {
  const isOwner =
    wallet.toLowerCase() === owner.toLowerCase();

  $("pauseBtn").disabled = !isOwner || isPaused;
  $("unpauseBtn").disabled = !isOwner || !isPaused;
  $("actionBtn").disabled = isPaused;
}

async function refreshStatus() {
  const owner = await contract.owner();
  const isPaused = await contract.paused();

  $("contractStatus").textContent =
    isPaused ? "Paused" : "Active";

  $("ownerAddress").textContent = "Owner: " + owner;

  updateButtons(owner, isPaused);
}

async function connectWallet() {
  try {
    if (!window.ethereum) {
      throw new Error("MetaMask is not installed.");
    }

    if (!ethers.isAddress(CONTRACT_ADDRESS)) {
      throw new Error("Contract address is not configured.");
    }

    provider = new ethers.BrowserProvider(window.ethereum);

    await provider.send("eth_requestAccounts", []);

    const network = await provider.getNetwork();

    if (network.chainId !== CHAIN_ID) {
      throw new Error("Please select Portaldot V3 Testnet.");
    }

    signer = await provider.getSigner();
    wallet = await signer.getAddress();

    const code = await provider.getCode(CONTRACT_ADDRESS);

    if (code === "0x") {
      throw new Error("Contract not found on this network.");
    }

    contract = new ethers.Contract(
      CONTRACT_ADDRESS,
      ABI,
      signer
    );

    $("walletAddress").textContent = wallet;

    await refreshStatus();
    showStatus("Wallet connected successfully.");

  } catch (error) {
    showStatus(error.shortMessage || error.message);
  }
}

async function sendTransaction(method) {
  try {
    if (!contract) {
      throw new Error("Connect your wallet first.");
    }

    showStatus("Waiting for MetaMask...");
    $("txLink").hidden = true;

    const tx = await contract[method]();

    showStatus("Transaction submitted: " + tx.hash);

    $("txLink").href = EXPLORER + "/tx/" + tx.hash;
    $("txLink").hidden = false;

    const receipt = await tx.wait();

    if (receipt.status !== 1) {
      throw new Error("Transaction failed.");
    }

    showStatus("Transaction confirmed: " + tx.hash);

    await refreshStatus();

  } catch (error) {
    showStatus(error.shortMessage || error.message);
  }
}

$("connectBtn").onclick = connectWallet;
$("pauseBtn").onclick = () => sendTransaction("pause");
$("unpauseBtn").onclick = () => sendTransaction("unpause");
$("actionBtn").onclick = () => sendTransaction("protectedAction");

if (window.ethereum) {
  window.ethereum.on("accountsChanged", () => location.reload());
  window.ethereum.on("chainChanged", () => location.reload());
}
