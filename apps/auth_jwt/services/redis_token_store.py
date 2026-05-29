from __future__ import annotations
import json
from datetime import datetime, timezone
from utils.redis_client import get_redis_client
from apps.auth_jwt.exceptions import SessionStateMismatchError, PipelineSessionRequiredError

class TokenRevokeReason:
    """
    Причины добавления токена в blacklist
    """
    ROTATION = 'rotation'
    LOGOUT = 'logout'
    LOGOUT_ALL = 'logout_all'
    REUSE_DETECTED = 'reuse_detected'
    TOKEN_MISMATCH = 'token_mismatch'


class RedisTokenStore:
    """
    Класс для работы с токенами и сессией Redis
    """
    REFRESH_WHITE_LIST = 'jwt:white:refresh:'
    BLACK_LIST = 'jwt:black:'
    SESSION_LIST = 'jwt:session:'
    USER_SESSIONS_LIST = 'jwt:user_sessions:'


    def __init__(self, redis_client=None) -> None:
        self.redis_client = redis_client or get_redis_client()


    @staticmethod
    def seconds_until_exp(exp_timestamp: int) -> int:
        """
        Оставшиеся время жизни токена в секундах
        """
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp_timestamp - now
        return max(ttl, 1)


    #---------------------------------------------------------------------
    # Формирование ключей
    #---------------------------------------------------------------------
    def refresh_whitelist_key(self, *, jti: str) -> str:
        """
        Получение REFRESH_WHITE_LIST
        """
        return f'{self.REFRESH_WHITE_LIST}{jti}'


    def blacklist_key(self, *, jti: str) -> str:
        """
        Получение BLACK_LIST
        """
        return f'{self.BLACK_LIST}{jti}'


    def session_key(self, *, session_id: str) -> str:
        """
        Получение SESSION_LIST
        """
        return f'{self.SESSION_LIST}{session_id}'


    def user_sessions_key(self, *, user_id: int) -> str:
        """
        Получение USER_SESSIONS_LIST
        """
        return f'{self.USER_SESSIONS_LIST}{user_id}'


    # ---------------------------------------------------------------------
    # Работа с Blacklist
    # ---------------------------------------------------------------------
    def add_to_blacklist(self, *, jti: str, exp: int, user_id: int, session_id: str,
                                  token_type: str, reason: str,
                                  client=None) -> None:
        """
        Добавление в blacklist
        """
        client = client or self.redis_client
        key = self.blacklist_key(jti=jti)
        ttl = self.seconds_until_exp(exp)
        revoked_at = int(datetime.now(timezone.utc).timestamp())
        value = {
            'user_id': user_id,
            'sid': session_id,
            'type': token_type,
            'revoked_at': revoked_at,
            'reason': reason,
        }

        client.set(key, json.dumps(value), ex=ttl)


    def is_blacklisted(self, *, jti: str) -> bool:
        """
        Проверка blacklist
        """
        return bool(self.redis_client.exists(self.blacklist_key(jti=jti)))


    def get_blacklist_metadata(self, *, jti: str) -> dict | None:
        """
        Получение metadata blacklist.
        """
        value = self.redis_client.get(self.blacklist_key(jti=jti))

        if not value:
            return None

        return json.loads(value)



    # ---------------------------------------------------------------------
    # Работа с Whitelist
    # ---------------------------------------------------------------------
    def add_refresh_to_whitelist(self, *, jti: str, user_id: int, session_id: str, exp: int, client=None) -> None:
        """
        Добавление refresh токена к whitelist
        """
        client = client or self.redis_client
        key = self.refresh_whitelist_key(jti=jti)
        ttl = self.seconds_until_exp(exp)
        value = {
           'user_id': user_id,
           'sid': session_id,
           'type': 'refresh',
        }
        client.set(key, json.dumps(value), ex=ttl)


    def is_refresh_whitelisted(self, *, jti: str) -> bool:
        """
        Проверка refresh в whitelist
        """
        return bool(self.redis_client.exists(self.refresh_whitelist_key(jti=jti)))


    def remove_refresh_from_whitelist(self, *, jti: str, client=None) -> None:
        """
        Удаление refresh из whitelist
        """
        client = client or self.redis_client
        client.delete(self.refresh_whitelist_key(jti=jti))


    # ---------------------------------------------------------------------
    # Работа с сессией
    # ---------------------------------------------------------------------
    def get_session(self, *, session_id: str) -> dict | None:
        """
        Получение сессии из Redis
        """
        session = self.redis_client.get(self.session_key(session_id=session_id))
        if not session:
            return None

        session_data = json.loads(session)
        if session_data.get('sid') != session_id:
            raise SessionStateMismatchError("Redis сессия повреждёна: sid не соответствует ключу.")

        return session_data


    def get_user_session_ids(self, *, user_id: int) -> list[str]:
        """
        Получение перечня сессий пользователя
        """
        key = self.user_sessions_key(user_id=user_id)
        values = self.redis_client.smembers(key)
        return [str(value) for value in values]


    def create_session(self, *, user_id: int, session_id: str,
                                access_jti: str, access_exp: int,
                                refresh_jti: str, refresh_exp: int,
                                client=None) -> None:
        """
        Создание сессии пользователя в Redis.
        """
        client = client or self.redis_client
        session_key = self.session_key(session_id=session_id)
        user_sessions_key = self.user_sessions_key(user_id=user_id)
        ttl = self.seconds_until_exp(refresh_exp)
        value = {
            'sid': session_id,
            'user_id': user_id,
            'access_jti': access_jti,
            'access_exp': access_exp,
            'refresh_jti': refresh_jti,
            'refresh_exp': refresh_exp,
        }

        client.set(session_key, json.dumps(value), ex=ttl)
        client.sadd(user_sessions_key, session_id)
        client.expire(user_sessions_key, ttl)


    def update_session_tokens(self, *, session_id: str,
                                       access_jti: str, access_exp: int,
                                       refresh_jti: str, refresh_exp: int,
                                       session: dict | None = None, client = None) -> None:
        """
        Обновление токенов сессии.

        ! Для работы через pipe, session является обязательным
        """
        if client and session is None:
            raise PipelineSessionRequiredError("session является обязательной при указании client")

        if session and session.get('sid') != session_id:
                raise SessionStateMismatchError("Сессия не соответствует id.")

        session = session or self.get_session(session_id=session_id)
        client = client or self.redis_client

        if not session:
            return

        session['access_jti'] = access_jti
        session['access_exp'] = access_exp
        session['refresh_jti'] = refresh_jti
        session['refresh_exp'] = refresh_exp

        session_key = self.session_key(session_id=session_id)
        user_sessions_key = self.user_sessions_key(user_id=session['user_id'])
        ttl = self.seconds_until_exp(refresh_exp)

        client.set(session_key, json.dumps(session), ex=ttl)
        client.expire(user_sessions_key, ttl)


    def delete_session(self, *, session_id: str, session: dict|None=None, client=None) -> None:
        """
        Удаление сессии.

        ! Для работы через pipe, session является обязательным
        """
        if client and session is None:
            raise PipelineSessionRequiredError("session является обязательной при указании client")

        if session and session.get('sid') != session_id:
                raise SessionStateMismatchError("Сессия не соответствует id.")

        session = session or self.get_session(session_id=session_id)
        client = client or self.redis_client

        if session:
            user_sessions_key = self.user_sessions_key(user_id=session['user_id'])
            client.srem(user_sessions_key, session_id)
        client.delete(self.session_key(session_id=session_id))


    def revoke_session(self, *, session_id: str, reason: str) -> None:
        """
        Полный отзыв сессии.

        - Добавляет токены access/refresh в blacklist
        - Удаляет refresh токен из whitelist;
        - Удаляет session key и session_id из user_sessions пользователя.
        """
        session = self.get_session(session_id=session_id)

        if not session:
            return

        user_id = int(session['user_id'])
        access_jti = session.get('access_jti')
        access_exp = session.get('access_exp')

        refresh_jti = session.get('refresh_jti')
        refresh_exp = session.get('refresh_exp')

        if access_jti and access_exp:
            self.add_to_blacklist(jti=access_jti,
                                  exp=access_exp,
                                  user_id=user_id,
                                  session_id=session_id,
                                  token_type='access',
                                  reason=reason)

        if refresh_jti and refresh_exp:
            self.remove_refresh_from_whitelist(jti=refresh_jti)
            self.add_to_blacklist(jti=refresh_jti,
                                  exp=refresh_exp,
                                  user_id=user_id,
                                  session_id=session_id,
                                  token_type='refresh',
                                  reason=reason)

        self.delete_session(session_id=session_id, session=session)