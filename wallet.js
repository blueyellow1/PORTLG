
(() => {
const RPC = "https://test-evm-rpc-v3.portaldot.dev";
const CHAIN = 420420777n;
const EXPLORER = "https://scanner-testnet-v3.portaldot.dev";
let provider, signer, address;

const el = id => document.getElementById(id);
const alertMsg = msg => el("plgAlert").textContent = msg;

function history() {
  const items = JSON.parse(localStorage.getItem("portlg_transactions") || "[]");
  const box = el("plgHistory");
  box.replaceChildren();

  if (!items.length) {
    box.textContent = "No transactions yet.";
    return;
  }

  items.forEach(item => {
    const div = document.createElement("div");
    div.style.cssText = "padding:12px;border-bottom:1px solid #445";

    const info = document.createElement("p");
    info.textContent = `${item.amount} tPOT — ${item.status}`;
    const link = document.createElement("a");
    link.href = EXPLORER + "/tx/" + encodeURIComponent(item.hash);
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "View on Blockchain Explorer";

    div.append(info, link);
    box.append(div);
  });
}

async function connect() {
  try {
    if (!window.ethereum) throw Error("Install MetaMask first.");

    provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []);

    let net = await provider.getNetwork();

    if (net.chainId !== CHAIN) {
      alertMsg("Wrong network! Switch to Portaldot V3 Testnet.");
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [{
          chainId: "0x" + CHAIN.toString(16),
          chainName: "Portaldot V3 Testnet",
          nativeCurrency: {name:"tPOT",symbol:"tPOT",decimals:18},
          rpcUrls:[RPC],
          blockExplorerUrls:[EXPLORER]
        }]
      });
      return;
    }

    signer = await provider.getSigner();
    address = await signer.getAddress();

    el("plgAddress").textContent = address;
    el("plgNetwork").textContent = "Portaldot V3 Testnet";

    const balance = await provider.getBalance(address);
    el("plgBalance").textContent = ethers.formatEther(balance) + " tPOT";

    alertMsg("Wallet connected successfully.");
  } catch(e) {
    alertMsg(e.shortMessage || e.message);
  }
}

async function send() {
  try {
    if (!signer) throw Error("Connect wallet first.");

    const to = el("plgRecipient").value.trim();
    const amount = el("plgAmount").value.trim();

    if (!ethers.isAddress(to)) throw Error("Invalid recipient address.");
    if (!amount || !Number.isFinite(Number(amount)) || Number(amount) <= 0)
      throw Error("Enter a valid amount.");

    const net = await provider.getNetwork();
    if (net.chainId !== CHAIN) throw Error("Wrong network. Sending blocked.");

    const value = ethers.parseEther(amount);
    const balance = await provider.getBalance(address);
    if (value > balance) throw Error("Insufficient balance for amount and gas.");

    alertMsg("Confirm transaction in MetaMask.");

    const tx = await signer.sendTransaction({to, value});

    const items = JSON.parse(localStorage.getItem("portlg_transactions") || "[]");
    items.unshift({hash:tx.hash, amount, status:"Pending"});
    localStorage.setItem("portlg_transactions", JSON.stringify(items.slice(0,50)));
    history();

    alertMsg("Transaction submitted. Waiting for confirmation.");

    const receipt = await tx.wait();
    if (receipt.status !== 1) throw Error("Transaction failed.");

    items[0].status = "Confirmed";
    localStorage.setItem("portlg_transactions", JSON.stringify(items.slice(0,50)));
    history();

    const balanceNow = await provider.getBalance(address);
    el("plgBalance").textContent = ethers.formatEther(balanceNow) + " tPOT";
    alertMsg("Transaction confirmed. Check Blockchain Explorer.");
  } catch(e) {
    alertMsg(e.shortMessage || e.message);
  }
}

el("plgConnect").addEventListener("click", connect);
el("plgSend").addEventListener("click", send);

el("plgCopy").addEventListener("click", async () => {
  if (!address) return alertMsg("Connect wallet first.");
  await navigator.clipboard.writeText(address);
  alertMsg("Address copied.");
});

history();
})();
