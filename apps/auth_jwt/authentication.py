# Copyright 2026 Nikolay Petukhov (NikPACodes)
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.
from __future__ import annotations
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from apps.auth_jwt.services.jwt_service import decode_token
from apps.auth_jwt.services.redis_token_store import RedisTokenStore
from apps.auth_jwt.exceptions import (InvalidAuthorizationHeaderError,
                                      InvalidTokenTypeError,
                                      BlacklistedTokenError,
                                      SessionNotFoundError,
                                      SessionTokenMismatchError,
                                      UserNotFoundAuthError)

User = get_user_model()

class JWTAuthentication(BaseAuthentication):
    """
    Кастомная аутентификация
    """
    keyword = b'Bearer'

    def __init__(self):
        self.token_store = RedisTokenStore()

    def authenticate(self, request):
        # Получаем заголовок
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if auth[0] != self.keyword:
            return None

        if len(auth) != 2:
            raise InvalidAuthorizationHeaderError()

        token = auth[1].decode('utf-8')
        payload = decode_token(token)

        # Проверяем access т.к.:
        # access -> для API
        # refresh -> ТОЛЬКО для обновления
        if payload['type'] != "access":
            raise InvalidTokenTypeError()

        jti = payload['jti']
        user_id = int(payload['sub'])
        session_id = payload['sid']

        # Проверяем наличие Access токена в черном списке
        if self.token_store.is_blacklisted(jti=jti):
            raise BlacklistedTokenError()

        # if not self.token_store.is_access_whitelisted(jti=jti):
        #     raise NotWhitelistedTokenError()

        # Проверяем соответствие Access токена сессии
        session = self.token_store.get_session(session_id=session_id)
        if not session:
            raise SessionNotFoundError()

        if session['access_jti'] != jti:
            raise SessionTokenMismatchError()


        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist as exc:
            raise UserNotFoundAuthError() from exc

        return user, payload