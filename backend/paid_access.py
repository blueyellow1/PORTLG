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
            CREATE TABLE IF NOT EXISTS paid_access_auth_attempts (
                ip_hash TEXT PRIMARY KEY,
                window_started_at INTEGER NOT NULL,
                failures INTEGER NOT NULL DEFAULT 0,
                blocked_until INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS paid_access_recovery_challenges (
                nonce TEXT PRIMARY KEY,
                wallet TEXT NOT NULL,
                message TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS paid_access_security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet TEXT NOT NULL DEFAULT '',
                event TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL
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
    if (
        not isinstance(transaction_hash, str)
        or len(transaction_hash) != 66
        or not transaction_hash.startswith("0x")
        or any(char not in "0123456789abcdefABCDEF" for char in transaction_hash[2:])
    ):
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



# Authentication abuse controls. The IP is hashed before storage; raw IPs are
# not persisted. Configure trusted proxy handling at the hosting layer.
AUTH_FAILURE_LIMIT = int(os.getenv("PORTLG_AUTH_FAILURE_LIMIT", "5"))
AUTH_WINDOW_SECONDS = int(os.getenv("PORTLG_AUTH_WINDOW_SECONDS", "600"))
AUTH_BLOCK_SECONDS = int(os.getenv("PORTLG_AUTH_BLOCK_SECONDS", "900"))


def _ip_digest(ip_address):
    if not isinstance(ip_address, str) or not ip_address:
        ip_address = "unknown"
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()


def check_auth_rate_limit(ip_address):
    """Return seconds remaining when an IP is blocked, otherwise zero."""
    now = int(time.time())
    digest = _ip_digest(ip_address)
    init_db()
    with _connect() as db:
        row = db.execute(
            "SELECT blocked_until FROM paid_access_auth_attempts WHERE ip_hash = ?",
            (digest,),
        ).fetchone()
        if row and row["blocked_until"] > now:
            return row["blocked_until"] - now
        return 0


def record_auth_failure(ip_address, wallet="", reason="Invalid wallet authentication"):
    """Throttle repeated failed signatures by source IP, not by target wallet.

    This avoids letting an attacker lock an unrelated victim's wallet merely
    by submitting invalid signatures against that wallet.
    """
    now = int(time.time())
    digest = _ip_digest(ip_address)
    init_db()
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM paid_access_auth_attempts WHERE ip_hash = ?", (digest,)
        ).fetchone()
        if row is None or now - row["window_started_at"] >= AUTH_WINDOW_SECONDS:
            failures = 1
            window_started = now
            blocked_until = 0
        else:
            failures = int(row["failures"]) + 1
            window_started = row["window_started_at"]
            blocked_until = now + AUTH_BLOCK_SECONDS if failures >= AUTH_FAILURE_LIMIT else row["blocked_until"]
        db.execute(
            """INSERT INTO paid_access_auth_attempts
               (ip_hash, window_started_at, failures, blocked_until)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(ip_hash) DO UPDATE SET
                 window_started_at=excluded.window_started_at,
                 failures=excluded.failures,
                 blocked_until=excluded.blocked_until""",
            (digest, window_started, failures, blocked_until),
        )
        db.execute(
            """INSERT INTO paid_access_security_logs(wallet, event, details, created_at)
               VALUES (?, ?, ?, ?)""",
            (str(wallet or "")[:42], "authentication_failure", str(reason)[:240], now),
        )
        return max(0, blocked_until - now)


def record_security_event(wallet, event, details=""):
    """Store a minimal security audit event; never store signatures or secrets."""
    now = int(time.time())
    wallet_value = str(wallet or "")[:42]
    with _connect() as db:
        db.execute(
            """INSERT INTO paid_access_security_logs(wallet, event, details, created_at)
               VALUES (?, ?, ?, ?)""",
            (wallet_value, str(event)[:80], str(details)[:240], now),
        )


def create_recovery_challenge(wallet):
    """Create a wallet-signature challenge to recover a temporarily locked account."""
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    wallet = Web3.to_checksum_address(wallet)
    now = int(time.time())
    init_db()
    with _connect() as db:
        user = db.execute(
            "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
        ).fetchone()
        if user is None:
            raise ValueError("No PORTLG Paid Access account exists for this wallet.")
        if user["locked_until"] <= now:
            raise ValueError("This account is not currently locked.")
        nonce = secrets.token_urlsafe(32)
        message = (
            "PORTLG Paid Access account recovery\n"
            f"Wallet: {wallet}\n"
            f"Network Chain ID: {CHAIN_ID}\n"
            f"Nonce: {nonce}\n"
            "Purpose: Request account recovery only. This message does not authorize a token transfer."
        )
        db.execute(
            """INSERT INTO paid_access_recovery_challenges
               (nonce, wallet, message, expires_at) VALUES (?, ?, ?, ?)""",
            (nonce, wallet, message, now + 5 * 60),
        )
    return {"wallet": wallet, "nonce": nonce, "message": message, "expiresIn": 300}


def recover_account(wallet, nonce, signature):
    """Unlock only after the locked wallet proves ownership with a fresh signature."""
    if not isinstance(wallet, str) or not Web3.is_address(wallet):
        raise ValueError("A valid wallet address is required.")
    if not isinstance(nonce, str) or not isinstance(signature, str):
        raise ValueError("A valid recovery nonce and signature are required.")
    wallet = Web3.to_checksum_address(wallet)
    now = int(time.time())
    init_db()
    with _connect() as db:
        challenge = db.execute(
            """SELECT * FROM paid_access_recovery_challenges
               WHERE nonce = ? AND wallet = ?""",
            (nonce, wallet),
        ).fetchone()
        if not challenge or challenge["consumed"] or challenge["expires_at"] < now:
            raise ValueError("This recovery request is invalid, expired or already used.")
        db.execute(
            "UPDATE paid_access_recovery_challenges SET consumed = 1 WHERE nonce = ?",
            (nonce,),
        )
        try:
            recovered = Account.recover_message(
                encode_defunct(text=challenge["message"]), signature=signature
            )
        except Exception as exc:
            raise ValueError("The recovery signature is invalid.") from exc
        if Web3.to_checksum_address(recovered) != wallet:
            raise ValueError("The recovery signature does not match this wallet.")
        cursor = db.execute(
            """UPDATE paid_access_users
               SET locked_until = 0, lock_reason = ''
               WHERE wallet = ? AND locked_until > ?""",
            (wallet, now),
        )
        if cursor.rowcount != 1:
            raise ValueError("The account is no longer locked or could not be recovered.")
        db.execute(
            """INSERT INTO paid_access_security_logs(wallet, event, details, created_at)
               VALUES (?, ?, ?, ?)""",
            (wallet, "account_recovered", "Wallet ownership re-verified with a fresh signature", now),
        )
        user = db.execute(
            "SELECT * FROM paid_access_users WHERE wallet = ?", (wallet,)
        ).fetchone()
        return _account_status(user, now)


def get_security_logs(limit=100):
    """Internal/admin use only. Do not expose this function without admin auth."""
    limit = max(1, min(int(limit), 500))
    init_db()
    with _connect() as db:
        rows = db.execute(
            """SELECT wallet, event, details, created_at
               FROM paid_access_security_logs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
