"""Security utilities for authentication."""

import secrets
import time
from datetime import timedelta

import bcrypt
from jose import JWTError, jwt

from hamlet.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (should include 'sub' for user ID)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (settings.access_token_expire_minutes * 60)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token() -> tuple[str, float]:
    """Create a refresh token.

    Returns:
        Tuple of (token_string, expiration_timestamp)
    """
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + (settings.refresh_token_expire_days * 24 * 60 * 60)
    return token, expires_at


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
