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
    def _seconds_until_exp(exp_timestamp: int) -> int:
        """
        Оставшиеся время жизни токена в секундах
        """
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp_timestamp - now
        return max(ttl, 1)


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


    def add_refresh_to_whitelist(self, *, jti: str, user_id: int, session_id: str, exp: int) -> None:
        """
        Добавление refresh токена к whitelist
        """
        key = f'{self.REFRESH_WHITE_LIST}{jti}'
        ttl = self._seconds_until_exp(exp)
        value = {
           'user_id': user_id,
           'sid': session_id,
           'type': 'refresh',
        }
        self.redis_client.set(key, json.dumps(value), ex=ttl)


    def add_to_blacklist(self, *, jti: str, exp: int) -> None:
        """
        Добавление в blacklist
        """
        key = f"{self.BLACK_LIST}{jti}"
        ttl = self._seconds_until_exp(exp)
        self.redis_client.set(key, "1", ex=ttl)


    # def is_access_whitelisted(self, *, jti: str) -> bool:
    #     """
    #     Проверка access в whitelist
    #     """
    #     return bool(self.redis_client.exists(f"{self.ACCESS_WHITE_LIST}{jti}"))


    def is_refresh_whitelisted(self, *, jti: str) -> bool:
        """
        Проверка refresh в whitelist
        """
        return bool(self.redis_client.exists(f"{self.REFRESH_WHITE_LIST}{jti}"))


    def is_blacklisted(self, *, jti: str) -> bool:
        """
        Проверка blacklist
        """
        return bool(self.redis_client.exists(f"{self.BLACK_LIST}{jti}"))


    def remove_access_from_whitelist(self, *, jti: str) -> None:
        """
        Удаление access из whitelist
        """
        self.redis_client.delete(f"{self.ACCESS_WHITE_LIST}{jti}")


    def remove_refresh_from_whitelist(self, *, jti: str) -> None:
        """
        Удаление refresh из whitelist
        """
        self.redis_client.delete(f"{self.REFRESH_WHITE_LIST}{jti}")


    def create_session(self, *, user_id: int, session_id: str,
                                access_jti: str, access_exp: int,
                                refresh_jti: str, refresh_exp: int) -> None:
        """
        Создание сессии пользователя в Redis.
        """
        session_key = f"{self.SESSION_LIST}{session_id}"
        user_sessions_key = f"{self.USER_SESSIONS_LIST}{user_id}"
        ttl = self._seconds_until_exp(refresh_exp)
        value = {
            'user_id': user_id,
            'access_jti': access_jti,
            'access_exp': access_exp,
            'refresh_jti': refresh_jti,
            'refresh_exp': refresh_exp,
        }

        self.redis_client.set(session_key, json.dumps(value), ex=ttl)
        self.redis_client.sadd(user_sessions_key, session_id)
        self.redis_client.expire(user_sessions_key, ttl)


    def get_session(self, *, session_id: str) -> dict | None:
        """
        Получение сессии из Redis
        """
        session = self.redis_client.get(f"{self.SESSION_LIST}{session_id}")
        if not session:
            return None
        return json.loads(session)


    def update_session_tokens(self, *, session_id: str,
                                       access_jti: str, access_exp: int,
                                       refresh_jti: str, refresh_exp: int) -> None:
        """
        Обновление токенов сессии
        """
        session = self.get_session(session_id=session_id)
        if not session:
            return

        session["access_jti"] = access_jti
        session["access_exp"] = access_exp
        session["refresh_jti"] = refresh_jti
        session["refresh_exp"] = refresh_exp

        session_key = f"{self.SESSION_LIST}{session_id}"
        user_sessions_key = f"{self.USER_SESSIONS_LIST}{session['user_id']}"
        ttl = self._seconds_until_exp(refresh_exp)

        self.redis_client.set(session_key, json.dumps(session), ex=ttl)
        self.redis_client.expire(user_sessions_key, ttl)


    def delete_session(self, *, session_id: str) -> None:
        """
        Удаление сессии
        """
        session = self.get_session(session_id=session_id)
        if session:
            user_sessions_key = f"{self.USER_SESSIONS_LIST}{session['user_id']}"
            self.redis_client.srem(user_sessions_key, session_id)
        self.redis_client.delete(f"{self.SESSION_LIST}{session_id}")


    def get_user_session_ids(self, *, user_id: int) -> list[str]:
        """
        Получение перечня сессий пользователя
        """
        key = f"{self.USER_SESSIONS_LIST}{user_id}"
        values = self.redis_client.smembers(key)
        return [value.decode("utf-8") for value in values]