import base64
import binascii
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from .database import SessionLocal
from . import models

PASSWORD_HASH_ITERATIONS = 120_000
SESSION_DURATION = timedelta(days=7)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")

    if salt is None:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_hex = salt.strip()
        if not salt_hex:
            raise ValueError("Salt must be non-empty")
        try:
            salt_bytes = bytes.fromhex(salt_hex)
        except ValueError as exc:
            raise ValueError("Salt must be a valid hex string") from exc

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PASSWORD_HASH_ITERATIONS,
    )
    return salt_hex, derived.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    if not salt or not expected_hash:
        return False
    try:
        _, candidate_hash = hash_password(password, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate_hash, expected_hash)


def build_session_token(user_id: int, secret: str) -> str:
    if not secret:
        raise ValueError("Session secret must be configured")

    expires_at = datetime.now(timezone.utc) + SESSION_DURATION
    payload = f"{user_id}:{int(expires_at.timestamp())}"
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")


def parse_session_token(token: str, secret: str) -> Optional[int]:
    if not token or not secret:
        return None
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        payload, signature = decoded.rsplit(":", 1)
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        user_id_str, expires_ts = payload.split(":", 1)
        expires_at = datetime.fromtimestamp(int(expires_ts), tz=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
        return int(user_id_str)
    except (ValueError, TypeError, binascii.Error):
        return None


def ensure_initial_admin(default_password: Optional[str] = None) -> None:
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        password = default_password or os.getenv("ADMIN_ACCESS_KEY")

    if not username or not password:
        return

    with SessionLocal() as db:
        existing = (
            db.query(models.AuthUser)
            .filter(models.AuthUser.username == username)
            .one_or_none()
        )
        if existing:
            needs_update = not verify_password(password, existing.salt, existing.password_hash)
            if needs_update:
                salt, password_hash = hash_password(password)
                existing.salt = salt
                existing.password_hash = password_hash
                existing.is_admin = True
                db.commit()
            elif not existing.is_admin:
                existing.is_admin = True
                db.commit()
            return

        salt, password_hash = hash_password(password)
        user = models.AuthUser(
            username=username,
            password_hash=password_hash,
            salt=salt,
            is_admin=True,
        )
        db.add(user)
        db.commit()
