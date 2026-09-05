from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import jwt
from loguru import logger
from pwdlib import PasswordHash

from app.core.config import get_settings

_ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def _get_secret() -> str:
    return get_settings().SECRET_KEY


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(password_hash.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(
        password_hash.verify, plain_password, hashed_password
    )


def create_access_token(
    subject: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    ttl = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + ttl

    payload: dict = {
        "sub": subject,
        "roles": roles,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }

    token = jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)
    logger.bind(subject=subject, roles=roles).debug("Access token created")
    return token


def decode_access_token(token: str) -> dict:
    payload: dict = jwt.decode(
        token,
        _get_secret(),
        algorithms=[_ALGORITHM],
        options={"require": ["sub", "exp", "roles"]},
    )
    return payload
