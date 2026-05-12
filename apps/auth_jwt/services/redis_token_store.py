from __future__ import annotations
import json
from datetime import datetime, timezone
from utils.redis_client import get_redis_client


class RedisTokenStore:
    """
    Класс для работы с токенами и сессией Redis
    """
    # ACCESS_WHITE_LIST = 'jwt:white:access:'
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
    # Проверки  Blacklist / Whitelist
    # ---------------------------------------------------------------------
    def is_refresh_whitelisted(self, *, jti: str) -> bool:
        """
        Проверка refresh в whitelist
        """
        return bool(self.redis_client.exists(self.refresh_whitelist_key(jti=jti)))


    def is_blacklisted(self, *, jti: str) -> bool:
        """
        Проверка blacklist
        """
        return bool(self.redis_client.exists(self.blacklist_key(jti=jti)))


    # def is_access_whitelisted(self, *, jti: str) -> bool:
    #     """
    #     Проверка access в whitelist
    #     """
    #     return bool(self.redis_client.exists(f"{self.ACCESS_WHITE_LIST}{jti}"))


    # ---------------------------------------------------------------------
    # Добавление в  Blacklist / Whitelist
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


    def add_to_blacklist(self, *, jti: str, exp: int, client=None) -> None:
        """
        Добавление в blacklist
        """
        client = client or self.redis_client
        key = self.blacklist_key(jti=jti)
        ttl = self.seconds_until_exp(exp)
        client.set(key, "1", ex=ttl)

    # def add_access_to_whitelist(self, *, jti: str, user_id: int, session_id: str, exp: int) -> None:
    #     """
    #     Добавление access токена к whitelist
    #     """
    #     key = f'{self.ACCESS_WHITE_LIST}{jti}'
    #     ttl = self._seconds_until_exp(exp)
    #     value = {
    #        'user_id': user_id,
    #        'sid': session_id,
    #        'type': 'access',
    #     }
    #     self.redis_client.set(key, json.dumps(value), ex=ttl)


    # ---------------------------------------------------------------------
    # Удаление из Blacklist / Whitelist
    # ---------------------------------------------------------------------
    def remove_refresh_from_whitelist(self, *, jti: str, client=None) -> None:
        """
        Удаление refresh из whitelist
        """
        client = client or self.redis_client
        client.delete(self.refresh_whitelist_key(jti=jti))


    # def remove_access_from_whitelist(self, *, jti: str) -> None:
    #     """
    #     Удаление access из whitelist
    #     """
    #     self.redis_client.delete(f"{self.ACCESS_WHITE_LIST}{jti}")


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
        return json.loads(session)


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
                                       refresh_jti: str, refresh_exp: int) -> None:
        """
        Обновление токенов сессии.

        ! Метод не предназначен для использования внутри pipeline transaction,
        т.к. сам читает session через обычный redis_client в get_session().
        """
        session = self.get_session(session_id=session_id)
        if not session:
            return

        session['access_jti'] = access_jti
        session['access_exp'] = access_exp
        session['refresh_jti'] = refresh_jti
        session['refresh_exp'] = refresh_exp

        session_key = self.session_key(session_id=session_id)
        user_sessions_key = self.user_sessions_key(user_id=session['user_id'])
        ttl = self.seconds_until_exp(refresh_exp)

        self.redis_client.set(session_key, json.dumps(session), ex=ttl)
        self.redis_client.expire(user_sessions_key, ttl)


    def delete_session(self, *, session_id: str) -> None:
        """
        Удаление сессии

        ! Не поддерживает работы через pipe, т.к.
        get_session() конфликтует с multi()
        """
        session = self.get_session(session_id=session_id)
        if session:
            user_sessions_key = self.user_sessions_key(user_id=session['user_id'])
            self.redis_client.srem(user_sessions_key, session_id)
        self.redis_client.delete(self.session_key(session_id=session_id))