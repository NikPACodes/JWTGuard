from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pathlib import Path
import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


def _read_private_key() -> str:
    """
    Считываем приватный ключ
    """
    path = Path(settings.JWT_PRIVATE_KEY_PATH)
    return path.read_text(encoding='utf-8')


def _read_public_key() -> str:
    """
    Считываем публичный ключ
    """
    path = Path(settings.JWT_PUBLIC_KEY_PATH)
    return path.read_text(encoding='utf-8')


def _build_payload(*, user_id: int, token_type: str, session_id: str, ttl_seconds: int) -> dict:
    """
    Сборка payload токена
    """
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds)
    return {
        'sub': str(user_id),
        'type': token_type,
        'jti': str(uuid4()),
        'sid': session_id,
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp()),
        'iss': settings.JWT_ISSUER,
    }


def create_access_token(*, user_id: int, session_id: str) -> tuple[str, dict]:
    """
    Создание access токена
    """
    payload = _build_payload(
        user_id=user_id,
        token_type='access',
        session_id=session_id,
        ttl_seconds=settings.JWT_ACCESS_TTL_SECONDS,
    )
    token = jwt.encode(payload=payload, key=_read_private_key(), algorithm=settings.JWT_ALGORITHM)
    return token, payload


def create_refresh_token(*, user_id: int, session_id: str) -> tuple[str, dict]:
    """
    Создание refresh токена
    """
    payload = _build_payload(
        user_id=user_id,
        token_type='refresh',
        session_id=session_id,
        ttl_seconds=settings.JWT_REFRESH_TTL_SECONDS,
    )
    token = jwt.encode(payload=payload, key=_read_private_key(), algorithm=settings.JWT_ALGORITHM)
    return token, payload


def decode_token(token: str) -> dict:
    """
    Расшифровка токена
    """
    try:
        payload = jwt.decode(
            token,
            _read_public_key(),
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed('Токен истек.')
    except jwt.InvalidIssuerError as exc:
        raise AuthenticationFailed('Ошибка издателя пользователя.')
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed('Некорректный токен.')

    required_fields = {'sub', 'type', 'jti', 'sid', 'iat', 'exp', 'iss',}
    if not required_fields.issubset(payload.keys()):
        raise AuthenticationFailed('Неполный payload токен.')

    return payload