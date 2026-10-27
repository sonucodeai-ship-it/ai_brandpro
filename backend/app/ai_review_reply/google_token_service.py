"""Encrypt/decrypt Google OAuth tokens at rest using a persistent Fernet key."""
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from .config import GOOGLE_TOKEN_ENCRYPTION_KEY


def _fernet() -> Fernet:
    if not GOOGLE_TOKEN_ENCRYPTION_KEY:
        raise RuntimeError("GOOGLE_TOKEN_ENCRYPTION_KEY is not configured.")
    try:
        return Fernet(GOOGLE_TOKEN_ENCRYPTION_KEY.encode("ascii"))
    except Exception as exc:
        raise RuntimeError(
            "GOOGLE_TOKEN_ENCRYPTION_KEY is invalid; it must be a Fernet key."
        ) from exc


def encrypt_token(token: str) -> str:
    if not token:
        raise ValueError("Cannot encrypt an empty token.")
    return _fernet().encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_token(token: str) -> str:
    if not token:
        raise ValueError("Encrypted token is empty.")
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored Google authorization data could not be decrypted.",
        ) from exc
