from __future__ import annotations
from uuid import uuid4
from django.contrib.auth import authenticate
from apps.auth_jwt.exceptions import (BlacklistedTokenError,
                                      InvalidCredentialsError,
                                      InvalidTokenTypeError,
                                      NotWhitelistedTokenError,
                                      SessionNotFoundError,
                                      SessionTokenMismatchError)
from apps.auth_jwt.services.jwt_service import create_access_token, create_refresh_token, decode_token
from apps.auth_jwt.services.redis_token_store import RedisTokenStore


def _remove_refresh(token_store: RedisTokenStore, *, jti: str, exp: int) -> None:
    """
    Отзыв refresh токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp)
    token_store.remove_refresh_from_whitelist(jti=jti)


def _remove_access(token_store: RedisTokenStore, *, jti: str, exp: int) -> None:
    """
    Отзыв access токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp)
    token_store.remove_access_from_whitelist(jti=jti)


def login_user(*, email: str, password: str, token_store: RedisTokenStore | None = None) -> dict:
    """
    Аутентификация пользователя и создание новой JWT-сессии.
    """
    token_store = token_store or RedisTokenStore()
    # Проверка учетных данных
    user = authenticate(username=email, password=password)
    if not user:
        raise InvalidCredentialsError()

    session_id = str(uuid4())

    access_token, access_payload = create_access_token(user_id=user.id, session_id=session_id)
    token_store.add_access_to_whitelist(
        jti=access_payload['jti'],
        user_id=user.id,
        session_id=session_id,
        exp=access_payload['exp'],
    )

    refresh_token, refresh_payload = create_refresh_token(user_id=user.id, session_id=session_id)
    token_store.add_refresh_to_whitelist(
        jti=refresh_payload['jti'],
        user_id=user.id,
        session_id=session_id,
        exp=refresh_payload['exp'],
    )

    token_store.create_session(
        session_id=session_id,
        user_id=user.id,
        access_jti=access_payload['jti'],
        access_exp=access_payload['exp'],
        refresh_jti=refresh_payload['jti'],
        refresh_exp=refresh_payload['exp'],
    )

    return {
        "access": access_token,
        "refresh": refresh_token,
    }


def refresh_tokens(*, refresh_token: str, token_store: RedisTokenStore | None = None) -> dict:
    """
    Обновление access и refresh токенов (rotation).
    """
    token_store = token_store or RedisTokenStore()
    payload = decode_token(refresh_token)

    if payload["type"] != "refresh":
        raise InvalidTokenTypeError()

    refresh_jti = payload['jti']
    refresh_exp = payload["exp"]
    session_id = payload['sid']
    user_id = int(payload['sub'])

    if token_store.is_blacklisted(jti=refresh_jti):
        raise BlacklistedTokenError("Refresh токен в blacklist.")
    if not token_store.is_refresh_whitelisted(jti=refresh_jti):
        raise NotWhitelistedTokenError("Refresh токена нет в whitelisted.")

    session = token_store.get_session(session_id=session_id)
    if not session:
        raise SessionNotFoundError()

    if session['refresh_jti'] != refresh_jti:
        raise SessionTokenMismatchError("Refresh токен не соответствует текущей сессии.")

    _remove_refresh(token_store, jti=refresh_jti, exp=refresh_exp)

    access_jti = session.get('access_jti')
    access_exp = session.get('access_exp')
    if access_jti and access_exp:
        _remove_access(token_store, jti=access_jti, exp=access_exp)

    new_access_token, new_access_payload = create_access_token(user_id=user_id, session_id=session_id)
    token_store.add_access_to_whitelist(
        jti=new_access_payload["jti"],
        user_id=user_id,
        session_id=session_id,
        exp=new_access_payload["exp"],
    )

    new_refresh_token, new_refresh_payload = create_refresh_token(user_id=user_id, session_id=session_id)
    token_store.add_refresh_to_whitelist(
        jti=new_refresh_payload["jti"],
        user_id=user_id,
        session_id=session_id,
        exp=new_refresh_payload["exp"],
    )

    token_store.update_session_tokens(
        session_id=session_id,
        access_jti=new_access_payload["jti"],
        access_exp=new_access_payload["exp"],
        refresh_jti=new_refresh_payload["jti"],
        refresh_exp=new_refresh_payload["exp"],
    )

    return {
        "access": new_access_token,
        "refresh": new_refresh_token,
    }


def logout_session(*, refresh_token: str, token_store: RedisTokenStore | None = None) -> None:
    """
    Logout текущей сессии пользователя.
    """
    token_store = token_store or RedisTokenStore()
    payload = decode_token(refresh_token)

    if payload['type'] != 'refresh':
        raise InvalidTokenTypeError()

    session_id = payload['sid']
    refresh_jti = payload['jti']
    refresh_exp = payload['exp']

    session = token_store.get_session(session_id=session_id)
    if not session:
        _remove_refresh(token_store, jti=refresh_jti, exp=refresh_exp)
        return

    _remove_refresh(token_store, jti=refresh_jti, exp=refresh_exp)

    access_jti = session.get('access_jti')
    access_exp = session.get('access_exp')
    active_refresh_jti = session.get('refresh_jti')
    active_refresh_exp = session.get('refresh_exp')

    if access_jti and access_exp:
        _remove_access(token_store, jti=access_jti, exp=access_exp)

    # Подстраховка на случай если active_refresh_jti != refresh_jti
    # Возможно в случае если refresh_jti украден и мы получили новый токен
    if active_refresh_jti and active_refresh_exp and active_refresh_jti != refresh_jti:
        _remove_refresh(token_store, jti=active_refresh_jti, exp=active_refresh_exp)

    token_store.delete_session(session_id=session_id)


def logout_all_sessions(*, user, token_store: RedisTokenStore | None = None) -> None:
    """
    Logout всех сессии пользователя.
    """
    token_store = token_store or RedisTokenStore()
    session_ids = token_store.get_user_session_ids(user_id=user.id)

    for session_id in session_ids:
        session = token_store.get_session(session_id=session_id)
        if not session:
            continue

        access_jti = session.get('access_jti')
        access_exp = session.get('access_exp')
        refresh_jti = session.get('refresh_jti')
        refresh_exp = session.get('refresh_exp')

        if access_jti and access_exp:
            _remove_access(token_store, jti=access_jti, exp=access_exp)

        if refresh_jti and refresh_exp:
            _remove_refresh(token_store, jti=refresh_jti, exp=refresh_exp)

        token_store.delete_session(session_id=session_id)