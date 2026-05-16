from __future__ import annotations
from uuid import uuid4
from django.contrib.auth import authenticate
from django.conf import settings
from datetime import datetime, timezone
import json
from redis.exceptions import WatchError
from apps.auth_jwt.exceptions import (BlacklistedTokenError,
                                      InvalidCredentialsError,
                                      InvalidTokenTypeError,
                                      NotWhitelistedTokenError,
                                      SessionNotFoundError,
                                      SessionTokenMismatchError,
                                      TokenRotationConflictError,
                                      SessionStateMismatchError,
                                      RefreshTokenReuseDetectedError)
from apps.auth_jwt.services.jwt_service import create_access_token, create_refresh_token, decode_token
from apps.auth_jwt.services.redis_token_store import RedisTokenStore, TokenRevokeReason


#--------------------------------------------------------------------------------------------------------
def _remove_refresh(token_store: RedisTokenStore, *, jti: str, exp: int,
                                                     user_id: int, session_id: str, reason: str,
                                                     client=None) -> None:
    """
    Отзыв refresh токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp, user_id=user_id, session_id=session_id,
                                 token_type='refresh', reason=reason,
                                 client=client)
    token_store.remove_refresh_from_whitelist(jti=jti, client=client)


def _remove_access(token_store: RedisTokenStore, *, jti: str, exp: int,
                                                    user_id: int, session_id: str, reason: str,
                                                    client=None) -> None:
    """
    Отзыв access токена
    """
    token_store.add_to_blacklist(jti=jti, exp=exp, user_id=user_id, session_id=session_id,
                                 token_type='access', reason=reason,
                                 client=client)


def _rotate_refresh_session(token_store: RedisTokenStore, *, user_id: int, session_id: str, refresh_jti: str,
                                                             new_access_payload: dict, new_refresh_payload: dict) -> None:
    """
    Атомарная ротация JWT-сессии через Redis WATCH/MULTI/EXEC.

    Защищает от ситуации, когда один refresh token одновременно
    используется в двух refresh-запросах.
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

            if session['sid'] != session_id:
                pipe.unwatch()
                raise SessionStateMismatchError("Redis сессия повреждёна: sid не соответствует ключу.")

            if session['refresh_jti'] != refresh_jti:
                pipe.unwatch()
                raise SessionTokenMismatchError("Refresh токен не соответствует текущей сессии.")

            access_jti = session.get('access_jti')
            access_exp = session.get('access_exp')
            refresh_exp = session.get('refresh_exp')


            # Открываем pipeline
            pipe.multi()

            _remove_refresh(token_store,
                            jti=refresh_jti,
                            exp=refresh_exp,
                            user_id=user_id,
                            session_id=session_id,
                            reason=TokenRevokeReason.ROTATION,
                            client=pipe)

            if access_jti and access_exp:
                _remove_access(token_store,
                               jti=access_jti,
                               exp=access_exp,
                               user_id=user_id,
                               session_id=session_id,
                               reason=TokenRevokeReason.ROTATION,
                               client=pipe)

            token_store.add_refresh_to_whitelist(jti=new_refresh_payload['jti'],
                                                 user_id=user_id,
                                                 session_id=session_id,
                                                 exp=new_refresh_payload['exp'],
                                                 client=pipe)

            token_store.update_session_tokens(session_id=session_id,
                                              access_jti=new_access_payload["jti"],
                                              access_exp=new_access_payload["exp"],
                                              refresh_jti=new_refresh_payload["jti"],
                                              refresh_exp=new_refresh_payload["exp"],
                                              session=session,
                                              client=pipe)
            # Закрытие pipeline и отправка команд
            pipe.execute()

    except WatchError:
        raise TokenRotationConflictError("Ошибка ротации Refresh токена.")


def _get_revoked_at(blacklist_metadata: dict) -> int:
    """
    Безопасное получение revoked_at из blacklist metadata.
    """
    revoked_at = blacklist_metadata.get("revoked_at")

    if not revoked_at:
        return 0

    return int(revoked_at)


def _blacklisted_refresh_token(token_store: RedisTokenStore, *, payload:dict, blacklist_metadata:dict|None) -> None:
    """
    Обработка ситуации, когда refresh token уже находится в blacklist.

    Если это недавняя rotation — считаем конфликтом/дублем запроса.
    Если нет — считаем reuse detection и отзываем сессию.
    """
    session_id = payload['sid']

    # Отзываем сессии с токенами без blacklist metadata
    # Подстраховка на случай поврежденных записей
    if not blacklist_metadata:
        token_store.revoke_session(session_id=session_id,
                                   reason=TokenRevokeReason.REUSE_DETECTED)
        raise RefreshTokenReuseDetectedError()

    reason = blacklist_metadata.get('reason')
    revoked_at = _get_revoked_at(blacklist_metadata)

    grace_seconds = settings.JWT_REFRESH_REUSE_GRACE_SECONDS
    seconds_after_revoke =int(datetime.now(timezone.utc).timestamp()) - revoked_at

    if reason == TokenRevokeReason.ROTATION and seconds_after_revoke <= grace_seconds:
        raise TokenRotationConflictError("Повторный refresh-запрос в пределах grace периода.")

    # Отзываем сессию
    token_store.revoke_session(session_id=session_id,
                               reason=TokenRevokeReason.REUSE_DETECTED)

    raise RefreshTokenReuseDetectedError()


#--------------------------------------------------------------------------------------------------------
def login_user(*, email: str, password: str, token_store: RedisTokenStore | None = None) -> dict:
    """
    Аутентификация пользователя и создание новой JWT-сессии.
    """
    token_store = token_store or RedisTokenStore()
    # Проверка учетных данных
    user = authenticate(username=email, password=password)
    if not user or not user.is_active:
        raise InvalidCredentialsError()

    session_id = str(uuid4())

    access_token, access_payload = create_access_token(user_id=user.id, session_id=session_id)
    refresh_token, refresh_payload = create_refresh_token(user_id=user.id, session_id=session_id)
    token_store.add_refresh_to_whitelist(jti=refresh_payload['jti'],
                                         user_id=user.id,
                                         session_id=session_id,
                                         exp=refresh_payload['exp'])

    token_store.create_session(session_id=session_id,
                               user_id=user.id,
                               access_jti=access_payload['jti'],
                               access_exp=access_payload['exp'],
                               refresh_jti=refresh_payload['jti'],
                               refresh_exp=refresh_payload['exp'])

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

    # Проверка blacklist для reuse detection
    blacklist_metadata = token_store.get_blacklist_metadata(jti=refresh_jti)
    if blacklist_metadata:
        _blacklisted_refresh_token(token_store,
                                   payload=payload,
                                   blacklist_metadata=blacklist_metadata)

    # Создаем новые токены сразу, но валидными они станут только после успешного Redis EXEC.
    new_access_token, new_access_payload = create_access_token(user_id=user_id, session_id=session_id)
    new_refresh_token, new_refresh_payload = create_refresh_token(user_id=user_id, session_id=session_id)

    try:
        _rotate_refresh_session(token_store,
                                user_id=user_id,
                                session_id=session_id,
                                refresh_jti=refresh_jti,
                                new_access_payload=new_access_payload,
                                new_refresh_payload=new_refresh_payload)

    # Т.к. мы уже провели reuse detection, то ошибка скорее всего вызвана race condition
    except (BlacklistedTokenError, NotWhitelistedTokenError):
        raise TokenRotationConflictError()

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
    user_id = int(payload['sub'])

    # Пред logout и отзывом, проверяем refresh токен
    if token_store.is_blacklisted(jti=refresh_jti):
        raise BlacklistedTokenError()

    if not token_store.is_refresh_whitelisted(jti=refresh_jti):
        raise NotWhitelistedTokenError()

    session = token_store.get_session(session_id=session_id)
    if not session:
        raise SessionNotFoundError()

    access_jti = session.get('access_jti')
    access_exp = session.get('access_exp')
    active_refresh_jti = session.get('refresh_jti')

    # Проверяем соответствие токена сессии
    if active_refresh_jti != refresh_jti:
        raise SessionTokenMismatchError()

    if access_jti and access_exp:
        _remove_access(token_store,
                       jti=access_jti,
                       exp=access_exp,
                       user_id=user_id,
                       session_id=session_id,
                       reason=TokenRevokeReason.LOGOUT)

    # Отзываем refresh токен
    _remove_refresh(token_store,
                    jti=refresh_jti,
                    exp=refresh_exp,
                    user_id=user_id,
                    session_id=session_id,
                    reason=TokenRevokeReason.LOGOUT)

    token_store.delete_session(session_id=session_id)


def logout_all_sessions(*, user, token_store: RedisTokenStore | None = None) -> None:
    """
    Logout всех сессии пользователя.
    """
    token_store = token_store or RedisTokenStore()
    session_ids = token_store.get_user_session_ids(user_id=user.id)

    for session_id in session_ids:
        token_store.revoke_session(session_id=session_id,
                                   reason=TokenRevokeReason.LOGOUT_ALL)