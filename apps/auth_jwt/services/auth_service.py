from __future__ import annotations
from uuid import uuid4
from django.contrib.auth import authenticate
import json
from redis.exceptions import WatchError
from apps.auth_jwt.exceptions import (BlacklistedTokenError,
                                      InvalidCredentialsError,
                                      InvalidTokenTypeError,
                                      NotWhitelistedTokenError,
                                      SessionNotFoundError,
                                      SessionTokenMismatchError,
                                      TokenRotationConflictError)
from apps.auth_jwt.services.jwt_service import create_access_token, create_refresh_token, decode_token
from apps.auth_jwt.services.redis_token_store import RedisTokenStore


def _remove_refresh(token_store: RedisTokenStore, *, jti: str, exp: int, client=None) -> None:
    """
    Отзыв refresh токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp, client=client)
    token_store.remove_refresh_from_whitelist(jti=jti, client=client)


def _remove_access(token_store: RedisTokenStore, *, jti: str, exp: int, client=None) -> None:
    """
    Отзыв access токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp, client=client)
    # token_store.remove_access_from_whitelist(jti=jti)


def _rotate_refresh_session(*, token_store: RedisTokenStore,
                            user_id: int, session_id: str, refresh_jti: str,
                            new_access_payload: dict, new_refresh_payload: dict) -> None:
    """
    Атомарная ротация JWT-сессии через Redis WATCH/MULTI/EXEC.

    Защищает от ситуации, когда один refresh token одновременно
    используется в двух refresh-запросах.

    Сессия обновляется вручную, т.к. update_session_tokens не поддерживает работу через pipeline transaction.
    """
    redis_client = token_store.redis_client

    session_key = token_store.session_key(session_id=session_id)
    refresh_key = token_store.refresh_whitelist_key(jti=refresh_jti)
    refresh_blacklist_key = token_store.blacklist_key(jti=refresh_jti)

    try:
        with redis_client.pipeline() as pipe:
            pipe.watch(session_key, refresh_key, refresh_blacklist_key)

            if pipe.exists(refresh_blacklist_key):
                pipe.unwatch()
                raise BlacklistedTokenError("Refresh токен в blacklist.")

            if not pipe.exists(refresh_key):
                pipe.unwatch()
                raise NotWhitelistedTokenError("Refresh токена нет в whitelisted.")

            raw_session = pipe.get(session_key)
            if not raw_session:
                pipe.unwatch()
                raise SessionNotFoundError()

            session = json.loads(raw_session)

            if session['refresh_jti'] != refresh_jti:
                pipe.unwatch()
                raise SessionTokenMismatchError("Refresh токен не соответствует текущей сессии.")

            access_jti = session.get('access_jti')
            access_exp = session.get('access_exp')
            refresh_exp = session.get('refresh_exp')


            session['access_jti'] = new_access_payload['jti']
            session['access_exp'] = new_access_payload['exp']
            session['refresh_jti'] = new_refresh_payload['jti']
            session['refresh_exp'] = new_refresh_payload['exp']

            new_refresh_ttl = token_store.seconds_until_exp(new_refresh_payload['exp'])

            # Открываем pipeline
            pipe.multi()

            _remove_refresh(token_store,
                            jti=refresh_jti,
                            exp=refresh_exp,
                            client=pipe)

            if access_jti and access_exp:
                _remove_access(token_store,
                               jti=access_jti,
                               exp=access_exp,
                               client=pipe)

            token_store.add_refresh_to_whitelist(jti=new_refresh_payload['jti'],
                                                 user_id=user_id,
                                                 session_id=session_id,
                                                 exp=new_refresh_payload['exp'],
                                                 client=pipe)

            pipe.set(session_key, json.dumps(session), ex=new_refresh_ttl)
            pipe.expire(token_store.user_sessions_key(user_id=user_id), new_refresh_ttl)
            # Закрытие pipeline и отправка команд
            pipe.execute()

    except WatchError:
        raise TokenRotationConflictError("Ошибка ротации Refresh токена.")


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
    # token_store.add_access_to_whitelist(
    #     jti=access_payload['jti'],
    #     user_id=user.id,
    #     session_id=session_id,
    #     exp=access_payload['exp'],
    # )

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

    if payload['type'] != 'refresh':
        raise InvalidTokenTypeError()

    refresh_jti = payload['jti']
    session_id = payload['sid']
    user_id = int(payload['sub'])

    # Создаем новые токены сразу, но валидными они станут только после успешного Redis EXEC.
    new_access_token, new_access_payload = create_access_token(user_id=user_id, session_id=session_id)
    new_refresh_token, new_refresh_payload = create_refresh_token(user_id=user_id, session_id=session_id)

    _rotate_refresh_session(
        token_store=token_store,
        user_id=user_id,
        session_id=session_id,
        refresh_jti=refresh_jti,
        new_access_payload=new_access_payload,
        new_refresh_payload=new_refresh_payload,
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

    # Пред logout и отзывом, проверяем refresh токен
    if token_store.is_blacklisted(jti=refresh_jti):
        raise BlacklistedTokenError()

    if not token_store.is_refresh_whitelisted(jti=refresh_jti):
        raise NotWhitelistedTokenError()

    session = token_store.get_session(session_id=session_id)
    if not session:
        raise SessionTokenMismatchError()

    access_jti = session.get('access_jti')
    access_exp = session.get('access_exp')
    active_refresh_jti = session.get('refresh_jti')

    # Проверяем соответствие токена сессии
    if active_refresh_jti != refresh_jti:
        raise SessionTokenMismatchError()

    if access_jti and access_exp:
        _remove_access(token_store, jti=access_jti, exp=access_exp)

    # Отзываем refresh токен
    _remove_refresh(token_store, jti=refresh_jti, exp=refresh_exp)

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