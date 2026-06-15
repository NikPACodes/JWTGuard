# Copyright 2026 Nikolay Petukhov (NikPACodes)
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.
from rest_framework.exceptions import AuthenticationFailed, APIException
from rest_framework import status


class JWTAuthError(AuthenticationFailed):
    default_detail = "Ошибка аутентификации."
    default_code = "authentication_failed"


class InvalidCredentialsError(JWTAuthError):
    default_detail = "Неверные учетные данные."
    default_code = "invalid_credentials"


class InvalidAuthorizationHeaderError(JWTAuthError):
    default_detail = "Неправильный заголовок Authorization."
    default_code = "invalid_authorization_header"


class InvalidTokenError(JWTAuthError):
    default_detail = "Некорректный токен."
    default_code = "invalid_token"


class ExpiredTokenError(JWTAuthError):
    default_detail = "Истекший токен."
    default_code = "token_expired"


class InvalidTokenIssuerError(JWTAuthError):
    default_detail = "Некорректный издатель токена."
    default_code = "invalid_token_issuer"


class InvalidTokenTypeError(JWTAuthError):
    default_detail = "Некорректный тип токена."
    default_code = "invalid_token_type"


class BlacklistedTokenError(JWTAuthError):
    default_detail = "Токен в blacklist."
    default_code = "token_blacklisted"


class NotWhitelistedTokenError(JWTAuthError):
    default_detail = "Токена нет в whitelist."
    default_code = "token_not_whitelisted"


class SessionNotFoundError(JWTAuthError):
    default_detail = "Сессия не найдена."
    default_code = "session_not_found"


class SessionTokenMismatchError(JWTAuthError):
    default_detail = "Токен не соответствует текущей сессии."
    default_code = "session_token_mismatch"


class UserNotFoundAuthError(JWTAuthError):
    default_detail = "Пользователь не найден или деактивирован."
    default_code = "user_not_found"


class TokenRotationConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Ошибка ротации токена."
    default_code = "token_rotation_conflict"


class RefreshTokenReuseDetectedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Обнаружено повторное использование Refresh токена. Сессия была отозвана."
    default_code = "refresh_token_reuse_detected"


class AuthServiceError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ошибка аутентификации."
    default_code = "auth_service_error"


class PipelineSessionRequiredError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Для операции через pipeline необходимо явно передать session."
    default_code = "pipeline_session_required"


class SessionStateMismatchError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Некорректное состояние Redis-сессии."
    default_code = "session_state_mismatch"
