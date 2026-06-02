# ✏️ DjangoJWT — API Examples

## 🎯 Назначение документа
Этот документ содержит примеры API-запросов для локальной проверки DjangoJWT.

Перед выполнением запросов убедись, что проект запущен:
```bash
make up-d
make migrate
make demo
```

ℹ️ Базовый URL для локального запуска `http://localhost:8000`

---

## Оглавление
- [DjangoJWT — API Examples](#-djangojwt--api-examples)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [API endpoints](#-api-endpoints)
    - [Auth](#auth)
    - [Content](#content)
    - [API documentation](#api-documentation)
    - [Health check](#health-check)
      - [Auth health](#auth-health)
      - [Content health](#content-health)
    - [Demo data](#demo-data)
    - [Register](#register)
    - [Login](#login)
    - [Profile](#profile)
    - [Refresh](#refresh)
    - [Refresh token reuse check](#refresh-token-reuse-check)
    - [Logout](#logout)
    - [Logout all sessions](#logout-all-sessions)
    - [Content list](#content-list)
    - [Content detail](#content-detail)
    - [Полный сценарий](#-полный-сценарий)
    - [Swagger / Redoc](#-swagger--redoc)
  - [Связанные документы](#-связанные-документы)

---

## 🌐 API endpoints

### Auth
```text
GET  /api/auth/health/
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
POST /api/auth/logout-all/
GET  /api/auth/profile/
```

### Content
```text
GET /api/content/health/
GET /api/content/
GET /api/content/{id}/
```

### API documentation
```text
GET /api/schema/
GET /api/schema/swagger/
GET /api/schema/redoc/
```

---

## Health check
### Auth health
```text
GET /api/auth/health/
```

Пример через `curl`:
```bash
curl -X GET http://localhost:8000/api/auth/health/
```


### Content health
```text
GET /api/content/health/
```

Пример через `curl`:
```bash
curl -X GET http://localhost:8000/api/content/health/
```

---

## Demo data
Перед регистрацией пользователя с ролью `role_1` или `role_2` нужно создать demo-данные:
```bash
make demo
```

Команда создаёт Django Groups:
- `role_1`
- `role_2`

и демонстрационный контент для проверки role-based access.

---

## Register
Создаёт пользователя и назначает ему указанную роль.
```text
POST /api/auth/register/
```

Content-Type: `application/json`  
Body:
```json
{
  "email": "user@example.com",
  "username": "user",
  "password": "StrongPass123!",
  "role": "role_1"
}
```

Пример через `curl`:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "StrongPass123!",
    "role": "role_1"
  }'
```

⚠️ ️Роль должна существовать в системе. Для локальной проверки сначала выполни `make demo`.

---

## Login
Возвращает пару токенов: access и refresh.
```text
POST /api/auth/login/
```

Content-Type: `application/json`  
Body:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Пример через `curl`:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123!"
  }'
```

Пример ответа:
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

---

## Profile
Проверяет доступ к защищённому endpoint по access token.
```text
GET /api/auth/profile/
```

Authorization: `Bearer <access_token>`

Пример через `curl`:
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```  

---

## Refresh
Обновляет пару токенов по refresh token.
```text
POST /api/auth/refresh/
```

Content-Type: `application/json`  
Body:
```json
{
  "refresh": "<refresh_token>"
}
```

Пример через `curl`:
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'
```

Пример ответа:
```json
{
  "access": "<new_access_token>",
  "refresh": "<new_refresh_token>"
}
```

ℹ️ После успешного refresh старая пара токенов становится недействительной.

---

## Refresh token reuse check
После успешного refresh старый refresh token больше не должен использоваться.

Сценарий проверки:
1. Выполнить login и получить `refresh_1`.
2. Выполнить refresh с `refresh_1` и получить `refresh_2`.
3. Повторно отправить `refresh_1`.

ℹ️ Повторное использование старого refresh token должно привести к ошибке или reuse-detection flow в зависимости от grace-периода и текущего состояния session.

---

## Logout
Завершает текущую сессию.
```text
POST /api/auth/logout/
```

Content-Type: `application/json`  
Body:
```json
{
  "refresh": "<refresh_token>"
}
```

Пример через `curl`:
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'
```

ℹ️ После logout:
- текущая session удаляется;
- access token добавляется в blacklist;
- refresh token добавляется в blacklist;
- refresh token удаляется из whitelist.

---

## Logout all sessions
Завершает все активные сессии текущего пользователя.
```text
POST /api/auth/logout-all/
```

Authorization: `Bearer <access_token>`

Пример через `curl`:
```bash
curl -X POST http://localhost:8000/api/auth/logout-all/ \
  -H "Authorization: Bearer <access_token>"
```

ℹ️ После logout all все старые access/refresh tokens пользователя должны стать недействительными.

---

## Content list
Возвращает список content-объектов, доступных группам текущего пользователя.
```text
GET /api/content/
```

Authorization: `Bearer <access_token>`

Пример через `curl`:
```bash
curl -X GET http://localhost:8000/api/content/ \
  -H "Authorization: Bearer <access_token>"
```

Пользователь с ролью `role_1` должен видеть:
- общий content;
- content для `role_1`.

Пользователь с ролью `role_2` должен видеть:
- общий content;
- content для `role_2`.

---

## Content detail
Возвращает конкретный content-объект, если он доступен текущему пользователю.
```text
GET /api/content/{id}/
```

Authorization: `Bearer <access_token>`

Пример через `curl`:
```bash
curl -X GET http://localhost:8000/api/content/1/ \
  -H "Authorization: Bearer <access_token>"
```

ℹ️ Если объект не доступен группам пользователя, API должен вернуть ошибку.

---

## 🔄 Полный сценарий

### 1. Создать demo-данные
```bash
make demo
```

### 2. Зарегистрировать пользователя
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "StrongPass123!",
    "role": "role_1"
  }'
```

### 3. Выполнить login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123!"
  }'
```
ℹ️ Сохрани access и refresh из ответа.

### 4. Проверить profile
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

### 5. Проверить content
```bash
curl -X GET http://localhost:8000/api/content/ \
  -H "Authorization: Bearer <access_token>"
```

### 6. Обновить токены
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'
```
ℹ️ Сохрани новую пару access / refresh.

### 7. Выполнить logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<new_refresh_token>"
  }'
```

### 8. Проверить, что старый access больше не работает
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <new_access_token>"
```
ℹ️ Ожидаемый результат — отказ в доступе.

---

## {···} Swagger / Redoc

OpenAPI schema ── `http://localhost:8000/api/schema/`  
Swagger UI ── `http://localhost:8000/api/schema/swagger/`  
Redoc ── `http://localhost:8000/api/schema/redoc/`  

ℹ️ Swagger можно использовать как альтернативу `curl` для ручной проверки endpoints.

---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [DEVELOPMENT](./DEVELOPMENT.md) ── Локальный запуск и команды разработки.
- [ARCHITECTURE](./ARCHITECTURE.md) ── Архитектура проекта.
- [JWT_FLOW](./JWT_FLOW.md) ── Жизненный цикл токенов.
- [SECURITY_MODEL](./SECURITY_MODEL.md) ── Модель безопасности.