"""Wallet-authenticated PORTLG Paid Access foundation.

This module stores trial/account state server-side. It never handles wallet
private keys; users prove wallet ownership by signing a one-time message.
"""
import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("PORTLG_PAID_ACCESS_DB", str(ROOT / "instance" / "paid_access.sqlite3")))
TRIAL_DAYS = int(os.getenv("PORTLG_TRIAL_DAYS", "7"))
INITIAL_CREDITS = int(os.getenv("PORTLG_INITIAL_CREDITS", "10"))
SESSION_HOURS = int(os.getenv("PORTLG_SESSION_HOURS", "12"))
CHAIN_ID = int(os.getenv("CHAIN_ID", "420420777"))


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS paid_access_users (
                wallet TEXT PRIMARY KEY,
                trial_started_at INTEGER NOT NULL,
                trial_ends_at INTEGER NOT NULL,
                credits_remaining INTEGER NOT NULL,
                locked_until INTEGER NOT NULL DEFAULT 0,
                lock_reason TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS paid_access_challenges (
                nonce TEXT PRIMARY KEY,
                wallet TEXT NOT NULL,
                message TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS paid_access_sessions (
                token_hash TEXT PRIMARY KEY,
                wallet TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS paid_access_sessions_wallet
                ON paid_access_sessions(wallet);
            CREATE TABLE IF NOT EXISTS paid_access_spent_transactions (
                transaction_hash TEXT PRIMARY KEY,
                wallet TEXT NOT NULL,
                action TEXT NOT NULL,
                spent_at INTEGER NOT NULL
            );
            """
        )


def create_challenge(wallet):
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    wallet = Web3.to_checksum_address(wallet)
    now = int(time.time())
    nonce = secrets.token_urlsafe(32)
    message = (
        "PORTLG Paid Access wallet verification\n"
        f"Wallet: {wallet}\n"
        f"Network Chain ID: {CHAIN_ID}\n"
        f"Nonce: {nonce}\n"
        "Purpose: Sign in only. This message does not authorize a token transfer."
    )
    init_db()
    with _connect() as db:
        db.execute(
            "INSERT INTO paid_access_challenges(nonce, wallet, message, expires_at) VALUES (?, ?, ?, ?)",
            (nonce, wallet, message, now + 5 * 60),
        )
    return {"wallet": wallet, "nonce": nonce, "message": message, "expiresIn": 300}


def verify_signature(wallet, nonce, signature):
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    if not isinstance(nonce, str) or not isinstance(signature, str):
        raise ValueError("A valid nonce and MetaMask signature are required.")
    wallet = Web3.to_checksum_address(wallet)
    now = int(time.time())
    init_db()
    with _connect() as db:
        challenge = db.execute(
            "SELECT * FROM paid_access_challenges WHERE nonce = ? AND wallet = ?",
            (nonce, wallet),
        ).fetchone()
        if not challenge or challenge["consumed"] or challenge["expires_at"] < now:
            raise ValueError("This sign-in request is invalid, expired or already used.")
        db.execute(
            "UPDATE paid_access_challenges SET consumed = 1 WHERE nonce = ?",
            (nonce,),
        )
        recovered = Account.recover_message(
            encode_defunct(text=challenge["message"]), signature=signature
        )
        if Web3.to_checksum_address(recovered) != wallet:
            raise ValueError("The MetaMask signature does not match this wallet.")

        user = db.execute(
            "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
        ).fetchone()
        if user is None:
            trial_end = now + TRIAL_DAYS * 24 * 60 * 60
            db.execute(
                """INSERT INTO paid_access_users
                   (wallet, trial_started_at, trial_ends_at, credits_remaining)
                   VALUES (?, ?, ?, ?)""",
                (wallet, now, trial_end, INITIAL_CREDITS),
            )
            user = db.execute(
                "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
            ).fetchone()

        if user["locked_until"] > now:
            raise PermissionError("This account is temporarily locked. Please contact support.")

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        db.execute(
            "INSERT INTO paid_access_sessions(token_hash, wallet, expires_at) VALUES (?, ?, ?)",
            (token_hash, wallet, now + SESSION_HOURS * 60 * 60),
        )
        return {"token": token, "account": _account_status(user, now)}


def _account_status(user, now=None):
    now = int(time.time()) if now is None else now
    locked = user["locked_until"] > now
    trial_active = now < user["trial_ends_at"]
    credits = int(user["credits_remaining"])
    return {
        "wallet": user["wallet"],
        "trialStartedAt": user["trial_started_at"],
        "trialEndsAt": user["trial_ends_at"],
        "trialActive": trial_active,
        "creditsRemaining": credits,
        "locked": locked,
        "lockedUntil": user["locked_until"] or None,
        "accessAllowed": (not locked) and trial_active and credits > 0,
    }


def get_session_account(token):
    if not isinstance(token, str) or not token:
        return None
    now = int(time.time())
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    init_db()
    with _connect() as db:
        row = db.execute(
            """SELECT u.* FROM paid_access_sessions s
               JOIN paid_access_users u ON u.wallet = s.wallet
               WHERE s.token_hash = ? AND s.expires_at > ?""",
            (token_hash, now),
        ).fetchone()
        return _account_status(row, now) if row else None


def lock_account(wallet, minutes=15, reason="Suspicious authenticated activity"):
    """Lock an authenticated account after a verified fraud signal."""
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    if not isinstance(minutes, int) or minutes < 1 or minutes > 1440:
        raise ValueError("Lock duration must be between 1 and 1440 minutes.")
    wallet = Web3.to_checksum_address(wallet)
    now = int(time.time())
    init_db()
    with _connect() as db:
        cursor = db.execute(
            "UPDATE paid_access_users SET locked_until = ?, lock_reason = ? WHERE wallet = ?",
            (now + minutes * 60, str(reason)[:240], wallet),
        )
        return cursor.rowcount == 1


def consume_credit(wallet, transaction_hash, action="protectedAction"):
    """Atomically debit one trial credit for one verified on-chain action."""
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    if not isinstance(transaction_hash, str) or len(transaction_hash) != 66 or not Web3.is_hex(transaction_hash):
        raise ValueError("A valid transaction hash is required.")
    if action != "protectedAction":
        raise ValueError("Credits can only be consumed by protectedAction.")
    wallet = Web3.to_checksum_address(wallet)
    tx_hash = transaction_hash.lower()
    now = int(time.time())
    init_db()
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        prior = db.execute(
            "SELECT 1 FROM paid_access_spent_transactions WHERE transaction_hash = ?",
            (tx_hash,),
        ).fetchone()
        if prior:
            return {"consumed": False, "reason": "transaction_already_used"}
        user = db.execute(
            "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
        ).fetchone()
        if user is None:
            return {"consumed": False, "reason": "account_not_found"}
        if user["locked_until"] > now:
            return {"consumed": False, "reason": "account_locked"}
        if user["trial_ends_at"] <= now:
            return {"consumed": False, "reason": "trial_expired"}
        if user["credits_remaining"] <= 0:
            return {"consumed": False, "reason": "no_credits"}
        db.execute(
            "UPDATE paid_access_users SET credits_remaining = credits_remaining - 1 WHERE wallet = ?",
            (wallet,),
        )
        db.execute(
            """INSERT INTO paid_access_spent_transactions
               (transaction_hash, wallet, action, spent_at) VALUES (?, ?, ?, ?)""",
            (tx_hash, wallet, action, now),
        )
        updated = db.execute(
            "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
        ).fetchone()
        return {"consumed": True, "account": _account_status(updated, now)}
