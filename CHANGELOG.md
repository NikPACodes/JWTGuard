# Changelog

## v1.0.0 - 2026-06-16

Первый release проекта DjangoJWT.

### Added

- Первый стабильный релиз DjangoJWT.
- JWT-аутентификация на основе RS256.
- Разделение access и refresh токенов.
- Refresh Token Rotation
- Refresh Token Reuse Detection
- Атомарная ротация refresh токена через Redis.
- Session revocation
- Logout из текущей сессии.
- Logout из всех сессий.
- Ролевой доступ через Django Groups и Permissions.
- Доступ к защищённому контенту на основе роли пользователя.
- Кастомная DRF-аутентификация.
- Кастомная обработка исключений.
- OpenAPI/Swagger-документация.
- Docker-окружение для локального запуска.
- Набор тестов на Pytest.
- GitHub Actions CI.
- Bruno-сценарии для проверки Auth, Content и Security flows.

### Notes

Этот релиз фиксирует завершённую учебную и reference-версию проекта, предназначенную
для портфолио и инженерной статьи о JWT-аутентификации, refresh token rotation, Redis-backed sessions и token reuse detection в Django.