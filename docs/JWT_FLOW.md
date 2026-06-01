# 🔁 DjangoJWT — JWT Flow

## 🎯 Назначение документа

Этот документ описывает основные сценарии работы JWT-аутентификации в проекте DjangoJWT:
- login;
- проверка access token;
- refresh rotation;
- refresh token reuse detection;
- logout текущей сессии;
- logout всех сессий пользователя.

---

## Оглавление

- [DjangoJWT — JWT Flow](#-djangojwt--jwt-flow)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [Общая модель](#-общая-модель)
  - [Token Payload](#-token-payload)
  - [Login Flow](#-login-flow)
    - [Последовательность](#последовательность)
    - [Итоговое состояние](#итоговое-состояние)
  - [Access Token Validation Flow](#-access-token-validation-flow)
    - [Проверки](#проверки)
    - [Почему проверяется Redis session](#почему-проверяется-redis-session)
    - [Access Token Validation Flow](#-access-token-validation-flow)
  - [Refresh Rotation Flow](#-refresh-rotation-flow)
    - [Проверки перед rotation](#проверки-перед-rotation)
    - [Изменения после успешной rotation](#изменения-после-успешной-rotation)
    - [Итоговое состояние](#итоговое-состояние-1)
  - [Atomic Refresh Rotation](#-atomic-refresh-rotation)
    - [Что происходит атомарно](#что-происходит-атомарно)
  - [Refresh Token Reuse Detection](#-refresh-token-reuse-detection)
    - [Нормальный сценарий](#нормальный-сценарий)
    - [Подозрительный сценарий](#подозрительный-сценарий)
    - [Grace-период](#grace-период)
    - [Реакция на reuse](#реакция-на-reuse)
    - [Итоговое состояние](#итоговое-состояние-2)
  - [Logout Flow](#-logout-flow)
    - [Проверки перед logout](#проверки-перед-logout)
    - [Итоговое состояние](#итоговое-состояние-3)
  - [Logout All Sessions Flow](#-logout-all-sessions-flow)
    - [Последовательность](#последовательность-1)
    - [Итоговое состояние](#итоговое-состояние-4)
  - [Redis Keys](#-redis-keys)
    - [Refresh Whitelist](#refresh-whitelist)
    - [Blacklist](#blacklist)
    - [Session Storage](#session-storage)
    - [User Sessions Index](#user-sessions-index)
  - [Итоговая схема](#-итоговая-схема)
  - [Связанные документы](#-связанные-документы)

---

## 🎯 Общая модель
Проект использует пару токенов:

- __Access token__ ── короткоживущий токен для доступа к API;
- __Refresh token__ ── долгоживущий токен для получения новой пары токенов.

Ключевая идея проекта:
```text
JWT + Redis Session State
```

__JWT__ ── используется как переносимый authentication credential.  
__Redis__ ── выступает источником актуального состояния сессии.

⚠️ Поэтому валидный JWT сам по себе не является достаточным условием доступа.  
Access token должен быть криптографически валиден и соответствовать активной Redis-сессии.

---

## 🧾 Token Payload
Access и Refresh tokens содержат общий набор базовых claims:
```json
{
  "sub": "user_id",
  "type": "access | refresh",
  "jti": "token_id",
  "sid": "session_id",
  "iat": 1710000000,
  "exp": 1710000900,
  "iss": "djangojwt"
}
```

Где:
- `sub` ── идентификатор пользователя;
- `type` ── тип токена: `access` или `refresh`;
- `jti` ── уникальный идентификатор конкретного токена;
- `sid` ── идентификатор пользовательской сессии;
- `iat` ── время выпуска токена;
- `exp` ── время истечения токена;
- `iss` ── issuer токена.

ℹ️ Значение `exp` зависит от типа токена: Access token имеет короткий TTL, Refresh token ── более длинный TTL.

---

## 🔐 Login Flow
Login создаёт новую JWT-сессию и возвращает клиенту пару токенов.
```text
Client
  ↓
POST /api/auth/login/
  ↓
Django authentication
  ↓
Create session_id
  ↓
Create access token
  ↓
Create refresh token
  ↓
Save refresh token to Redis whitelist
  ↓
Create Redis session state
  ↓
Add session_id to user sessions index
  ↓
Return access + refresh
```


### Последовательность
1. Клиент отправляет `email` и `password`.
2. Django проверяет credentials пользователя.
3. Создаётся новый `session_id`.
4. Генерируется Access token.
5. Генерируется Refresh token.
6. Refresh token сохраняется в Redis whitelist.
7. В Redis создаётся session state.
8. `session_id` добавляется в индекс сессий пользователя.
9. Клиент получает Access и Refresh tokens.


### Итоговое состояние
После успешного login:
```text
Клиент получает:
- access token
- refresh token

В Redis появляются записи:
- jwt:white:refresh:{refresh_jti}
- jwt:session:{sid}
- jwt:user_sessions:{user_id}
```

---

## 🛂 Access Token Validation Flow
Access token используется для доступа к защищённым API endpoints.
```text
Client
  ↓
Authorization: Bearer <access>
  ↓
Extract token
  ↓
Decode JWT
  ↓
Verify RS256 signature
  ↓
Verify exp
  ↓
Verify type=access
  ↓
Check blacklist
  ↓
Load Redis session by sid
  ↓
Compare access_jti
  ↓
Load active user
  ↓
Request authenticated
```


### Проверки
Access token считается валидным, если:
1. токен успешно декодирован;
2. `RS256` signature валиден;
3. `exp` не истёк;
4. `type == access`;
5. `jti` отсутствует в blacklist;
6. Redis session существует;
7. `payload.jti == session.access_jti`;
8. пользователь существует и активен.


### Почему проверяется Redis session
Access token не хранится в whitelist.  
Вместо этого используется проверка соответствия активной сессии:
```text
payload.jti == session.access_jti
```

Это позволяет инвалидировать Access token после:
- refresh rotation;
- logout;
- logout all sessions;
- session revoke;
- refresh token reuse detection.

---

## ♻️ Refresh Rotation Flow
Refresh token используется для получения новой пары Access / Refresh tokens.
```text
Client
  ↓
POST /api/auth/refresh/
  ↓
Decode refresh token
  ↓
Verify RS256 signature
  ↓
Verify exp
  ↓
Verify type=refresh
  ↓
Check blacklist
  ↓
Check whitelist
  ↓
Load Redis session
  ↓
Compare refresh_jti
  ↓
Atomic rotation
  ↓
Return new access + refresh
```


### Проверки перед rotation
Refresh token считается активным, если:
1. токен успешно декодирован;
2. `RS256` signature валиден;
3. `exp` не истёк;
4. `type == refresh`;
5. `jti` отсутствует в blacklist;
6. `jti` присутствует в Refresh whitelist;
7. Redis session существует;
8. `payload.jti == session.refresh_jti`.


### Изменения после успешной rotation
При успешном refresh:
1. старый Refresh token удаляется из whitelist;
2. старый Refresh token добавляется в blacklist;
3. старый Access token добавляется в blacklist;
4. генерируется новый Access token;
5. генерируется новый Refresh token;
6. новый Refresh token добавляется в whitelist;
7. Redis session обновляется новыми `access_jti` и `refresh_jti`;
8. клиент получает новую пару токенов.


### Итоговое состояние
```text
Old access:
- blacklisted

Old refresh:
- removed from whitelist
- blacklisted

New refresh:
- added to whitelist

Redis session:
- updated access_jti
- updated refresh_jti
```

---

## ⚛️ Atomic Refresh Rotation
Refresh rotation выполняется атомарно через Redis transaction pipeline.  
Это защищает от ситуации, когда один и тот же Refresh token используется двумя параллельными запросами.

⚠️ Проблемный сценарий без атомарности:
```text
Request A проверил old refresh
Request B проверил old refresh
Request A выпустил новую пару токенов
Request B выпустил ещё одну новую пару токенов
```

ℹ️ В проекте rotation выполняется как единая логическая операция.

Внутри atomic rotation проверяются и изменяются:
```text
jwt:session:{sid}
jwt:white:refresh:{old_refresh_jti}
jwt:black:{old_refresh_jti}
```


### Что происходит атомарно
```text
delete old refresh from whitelist
add old refresh to blacklist
add old access to blacklist
add new refresh to whitelist
update session state
```

⚠️ Если Redis transaction не может быть выполнена консистентно, refresh завершается ошибкой `token_rotation_conflict`.

---

## 🚨 Refresh Token Reuse Detection
Refresh Token Reuse Detection срабатывает, когда уже отозванный Refresh token используется повторно.


### Нормальный сценарий
```text
Refresh A активен
  ↓
Refresh A используется для rotation
  ↓
Refresh A удаляется из whitelist
  ↓
Refresh A добавляется в blacklist
  ↓
Refresh B становится активным
```


### Подозрительный сценарий
```text
Refresh A уже был использован
  ↓
Refresh A повторно отправлен на /api/auth/refresh/
  ↓
Refresh A найден в blacklist
  ↓
Система проверяет причину revoke
  ↓
Если это не технический дубль запроса ── session revoke
```


### Grace-период
В проекте используется настройка:
```dotenv
JWT_REFRESH_REUSE_GRACE_SECONDS
```

Она нужна для обработки технических дублей refresh-запроса сразу после успешной rotation.  
ℹ️ Если старый Refresh token повторно используется в пределах grace-периода после rotation, система возвращает ошибку конфликта rotation.  
ℹ️ Если старый Refresh token используется позже grace-периода, это считается reuse detection.


### Реакция на reuse
При reuse detection система:
1. определяет `sid` из payload старого Refresh token;
2. загружает активную Redis session;
3. удаляет текущий активный Refresh token из whitelist;
4. добавляет текущий Access token в blacklist;
5. добавляет текущий Refresh token в blacklist;
6. удаляет Redis session;
7. удаляет `sid` из индекса сессий пользователя;
8. возвращает ошибку `refresh_token_reuse_detected`.


### Итоговое состояние
```text
Affected session:
- revoked

Current access:
- blacklisted

Current refresh:
- removed from whitelist
- blacklisted

Redis session:
- deleted
```

---

## 🚪 Logout Flow
Logout завершает текущую сессию пользователя.

В проекте logout выполняется на основе Refresh token.  
Access token может отсутствовать или быть уже неактуальным.
```text
Client
  ↓
POST /api/auth/logout/
  ↓
Send refresh token
  ↓
Decode refresh token
  ↓
Verify type=refresh
  ↓
Check blacklist
  ↓
Check whitelist
  ↓
Load Redis session
  ↓
Compare refresh_jti
  ↓
Blacklist access token
  ↓
Blacklist refresh token
  ↓
Remove refresh from whitelist
  ↓
Delete Redis session
  ↓
Remove sid from user sessions index
  ↓
Session closed
```


### Проверки перед logout
Logout выполняется только если:
1. Refresh token успешно декодирован;
2. `type == refresh`;
3. Refresh token отсутствует в blacklist;
4. Refresh token присутствует в whitelist;
5. Redis session существует;
6. `payload.jti == session.refresh_jti`.


### Итоговое состояние
После logout:
```text
Access token:
- blacklisted

Refresh token:
- removed from whitelist
- blacklisted

Redis session:
- deleted

User sessions index:
- sid removed
```

---

## 🚪 Logout All Sessions Flow
Logout all завершает все активные сессии текущего пользователя.  
⚠️ Endpoint требует валидный Access token, потому что операция выполняется от имени уже аутентифицированного пользователя.
```text
Client
  ↓
POST /api/auth/logout-all/
  ↓
Access token authentication
  ↓
Load user sessions index
  ↓
For each session:
    load session
    blacklist access token
    blacklist refresh token
    remove refresh from whitelist
    delete session
  ↓
Clear active sessions for user
  ↓
All sessions closed
```


### Последовательность
1. Пользователь аутентифицируется по Access token.
2. Из Redis загружаются все `session_id` пользователя.
3. Для каждой session выполняется revoke.
4. Access token каждой session добавляется в blacklist.
5. Refresh token каждой session добавляется в blacklist.
6. Refresh token каждой session удаляется из whitelist.
7. Redis session удаляется.
8. `session_id` удаляется из индекса сессий пользователя.


### Итоговое состояние
После logout all:
```text
All user access tokens:
- blacklisted

All user refresh tokens:
- removed from whitelist
- blacklisted

All user sessions:
- deleted
```

---

## 🗃️ Redis Keys
В JWT flow участвуют следующие Redis keys.

### Refresh Whitelist
Хранит активные Refresh tokens.
```text
jwt:white:refresh:{jti}
```

Используется при:
- refresh validation;
- refresh rotation;
- logout;
- logout all sessions;
- session revoke.


### Blacklist
Хранит отозванные Access и Refresh tokens.
```text
jwt:black:{jti}
```

Используется при:
- access token validation;
- refresh token validation;
- refresh rotation;
- logout;
- logout all sessions;
- reuse detection.

Blacklist value содержит metadata revoke-события:
```json
{
  "user_id": 1,
  "sid": "session-id",
  "type": "refresh",
  "revoked_at": 1710000000,
  "reason": "rotation"
}
```


### Session Storage
Хранит актуальное состояние пользовательской сессии.
```text
jwt:session:{sid}
```

Пример:
```json
{
  "sid": "session-id",
  "user_id": 1,
  "access_jti": "access-token-jti",
  "access_exp": 1710000000,
  "refresh_jti": "refresh-token-jti",
  "refresh_exp": 1710500000
}
```


### User Sessions Index
Хранит список активных `sid` пользователя.
```text
jwt:user_sessions:{user_id}
```

Используется для:
- logout all sessions;
- поиска всех активных сессий пользователя;
- удаления session из пользовательского индекса.

---

## ✅ Итоговая схема
```text
Login
  ↓
Создаёт JWT session

Access validation
  ↓
Проверяет JWT + Redis session

Refresh rotation
  ↓
Атомарно заменяет пару токенов

Reuse detection
  ↓
Выявляет повторное использование старого refresh

Logout
  ↓
Удаляет текущую session

Logout all
  ↓
Удаляет все sessions пользователя
```

Итоговая модель:
```text
JWT передаёт claims
Redis подтверждает актуальность session
Whitelist контролирует refresh lifecycle
Blacklist отзывает токены
Rotation заменяет refresh token
Reuse detection отзывает скомпрометированную session
```

---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [ARCHITECTURE](./ARCHITECTURE.md) ── Архитектура проекта.
- [SECURITY_MODEL](./SECURITY_MODEL.md) ── Модель безопасности.
- [DEVELOPMENT](./DEVELOPMENT.md) ── Локальный запуск и команды разработки.
- [API_EXAMPLES](./API_EXAMPLES.md) ── Примеры API-запросов.
