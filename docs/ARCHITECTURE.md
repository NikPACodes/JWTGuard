# 🏗️ DjangoJWT — Архитектура проекта

## 🎯 Назначение документа

Этот документ описывает архитектуру проекта DjangoJWT: основные модули, границы ответственности, 
ключевые технические решения и причины выбора текущего подхода.

---

## Оглавление
- [DjangoJWT — Архитектура проекта](#-djangojwt--архитектура-проекта)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [Общая идея и цели проекта](#-общая-идея-и-цели-проекта)
  - [Технологический стек](#-технологический-стек)
  - [Тестирование](#-тестирование)
  - [Высокоуровневая схема](#-высокоуровневая-схема)
    - [Client](#client)
    - [DRF API](#drf-api)
    - [Authentication Layer](#authentication-layer)
    - [Auth Service](#auth-service)
    - [JWT Service](#jwt-service)
    - [Redis Token Store](#redis-token-store)
  - [Приложения проекта](#-приложения-проекта)
    - [apps.users](#appsusers)
    - [apps.auth_jwt](#appsauth_jwt)
    - [apps.content](#appscontent)
  - [Access и Refresh tokens](#-access-и-refresh-tokens)
    - [Access token](#access-token)
    - [Refresh token](#refresh-token)
  - [Почему access whitelist не используется](#-почему-access-whitelist-не-используется)
  - [Redis Session Model](#-redis-session-model)
  - [Структура Redis Keys](#-структура-redis-keys)
    - [Refresh Whitelist](#refresh-whitelist)
    - [Blacklist](#blacklist)
    - [Session Storage](#session-storage)
    - [User Sessions Index](#user-sessions-index)
  - [Атомарность Refresh Rotation](#-атомарность-refresh-rotation)
  - [Refresh Token Reuse Detection](#-refresh-token-reuse-detection)
  - [Почему PyJWT, а не SimpleJWT](#-почему-pyjwt-а-не-simplejwt)
  - [Почему RS256](#-почему-rs256)
  - [PostgreSQL и Redis](#-postgresql-и-redis)
    - [PostgreSQL](#postgresql)
    - [Redis](#redis)
  - [Роли и контент](#-роли-и-контент)
  - [Возможность выделения auth-service](#-возможность-выделения-auth-service)
  - [Связанные документы](#-связанные-документы)
  - [Итог](#-итог)

---

## 🎯 Общая идея и цели проекта

DjangoJWT реализует управляемую JWT-аутентификацию на базе стека:
- _Django_
- _Django REST Framework_
- _PyJWT_
- _Redis_
- _PostgreSQL_

Ключевая архитектурная идея:
```text
JWT + Redis Session State
```

__JWT__ — используется как переносимый authentication credential.  
__Redis__ — выступает источником актуального состояния сессии.

ℹ️ Проект не является полностью stateless JWT-реализацией. 
Access token должен быть не только криптографически валиден, но и соответствовать активной Redis-сессии.

Основные цели:
- реализовать JWT-auth без готового SimpleJWT flow;
- использовать `PyJWT` для полного контроля над payload и жизненным циклом токенов;
- использовать `RS256` вместо shared-secret подхода;
- хранить runtime-состояние сессий в Redis;
- реализовать logout до истечения JWT;
- реализовать refresh token whitelist;
- реализовать token blacklist;
- реализовать atomic refresh rotation;
- реализовать refresh token reuse detection;
- показать демонстрационный RBAC через Django Groups;
- сохранить возможность дальнейшего выделения auth-ядра в отдельный сервис.

---

## 🏗️ Технологический стек

- Python 3.12
- Django
- Django REST Framework
- PyJWT
- Redis
- PostgreSQL
- Docker / Docker Compose
- Pytest
- drf-spectacular
- Bruno

---

## ⚡ Тестирование
Проект использует несколько уровней проверки:
- __Pytest__ ── автоматические тесты бизнес-логики и security-сценариев;
- __GitHub Actions__ ── автоматическая проверка проекта в CI;
- __Swagger UI__ ── интерактивное исследование API;
- __Bruno__ ── воспроизведение готовых пользовательских сценариев через HTTP-запросы.

ℹ️ __Bruno__ не является частью runtime-архитектуры проекта и используется исключительно
как вспомогательный инструмент демонстрации и ручного тестирования API.

---

## 📜 Высокоуровневая схема

```text
Client
  ↓
DRF API
  ↓
Authentication Layer
  ↓
Auth Service
  ↓
JWT Service / Redis Token Store
  ↓
PostgreSQL / Redis
```


### Client
Клиент хранит access / refresh token и использует:
- _access token_ — для API-запросов;
- _refresh token_ — для получения новой пары токенов;
- _refresh token_ — для logout текущей сессии.


### DRF API
API-слой отвечает за:
- приём HTTP-запросов;
- сериализацию и валидацию входных данных;
- возврат HTTP-ответов;
- делегирование бизнес-логики в сервисный слой.

ℹ️ API-слой не должен содержать сложную token/session-логику.


### Authentication Layer
Кастомный authentication layer отвечает за проверку access token на защищённых endpoints.

Он выполняет:
- извлечение Bearer token;
- декодирование JWT;
- проверку token type;
- проверку blacklist;
- проверку Redis session state;
- проверку соответствия `payload.jti == session.access_jti`;
- загрузку пользователя.


### Auth Service
Auth Service координирует основную бизнес-логику аутентификации:
- login;
- refresh;
- logout;
- logout all sessions;
- revoke session;
- refresh token reuse detection.

ℹ️ Именно этот слой связывает JWT Service и Redis Token Store в единый auth-flow.


### JWT Service
JWT Service отвечает только за работу с JWT:
- создание access token;
- создание refresh token;
- формирование payload;
- декодирование токенов через `jwt.decode()`;
- проверку RS256-подписи через public key;
- автоматическую проверку `exp` при декодировании;
- проверку `iss` через `issuer=settings.JWT_ISSUER`;
- преобразование ошибок PyJWT в доменные auth-исключения.

ℹ️ JWT Service не знает детали хранения сессий в Redis. 
Проверка подписи, expiration и issuer выполняется библиотекой PyJWT внутри `decode_token()`.


### Redis Token Store
Redis Token Store отвечает за runtime-состояние auth-flow:
- refresh whitelist;
- token blacklist;
- session state;
- user sessions index;
- Redis key builders;
- Redis-операции для revoke и refresh rotation.

ℹ️ Atomic refresh rotation координируется Auth Service, 
а Redis Token Store предоставляет операции для работы с Redis-состоянием.

---

## 📱 Приложения проекта

### apps.users
Содержит кастомную модель пользователя.

__Email__ используется как основной идентификатор для аутентификации:
```text
USERNAME_FIELD = "email"
```

ℹ️ __Username__ сохраняется как дополнительное уникальное поле.


### apps.auth_jwt
Основное JWT-auth ядро проекта.

Содержит:
- API endpoints;
- serializers;
- authentication class;
- auth service;
- JWT service;
- Redis token store;
- exceptions;
- management command для demo-данных;
- tests auth-flow.


### apps.content
Демонстрационный content-модуль.

Его задача — показать, как JWT-аутентификация и Django Groups могут использоваться для защиты ресурсов.

⚠️ Content-модуль не является основной бизнес-доменной частью проекта.

---

## 🔑 Access и Refresh tokens
Система использует два типа JWT-токенов:
- _access token_
- _refresh token_

### Access token
Access token используется для авторизации API-запросов.

Свойства:
- короткий TTL;
- подпись `RS256`;
- содержит `sub`, `sid`, `jti`, `type`;
- _НЕ хранится_ в whitelist;
- может быть добавлен в blacklist при logout, rotation или revoke;
- проверяется через Redis session state.

ℹ️ Access token не хранится в whitelist намеренно.
Его актуальность контролируется через короткий TTL, blacklist и соответствие активной Redis-сессии.


### Refresh token
Refresh token используется для получения новой пары токенов.

Свойства:
- более длинный TTL;
- подпись `RS256`;
- содержит `sub`, `sid`, `jti`, `type`;
- хранится в Redis whitelist;
- связан с активной session;
- ротируется при refresh;
- добавляется в blacklist после revoke/rotation.

ℹ️ Refresh token является главным долгоживущим credential системы, поэтому контролируется строже, чем access token.

---

## ❓ Почему access whitelist не используется
Проект намеренно не использует _whitelist_ для _access token_.

Причины:
- access token короткоживущий;
- _whitelist_ создаёт дополнительную нагрузку на _Redis_;
- access token можно отозвать через _blacklist_;
- каждый API-запрос потребовал бы дополнительного Redis lookup;
- главным долгоживущим credential системы является refresh token.

Вместо этого _access token_ проходит:
1. проверку `RS256` _signature_;
2. проверку _expiration_;
3. проверку _token type_;
4. проверку _blacklist_;
5. проверку _Redis session_;
6. проверку соответствия `access_jti` активной _session state_.

ℹ️ Такой подход сохраняет управляемость сессии без хранения каждого access token в отдельном whitelist.

---

## 🪪 Redis Session Model
Redis выступает в качестве `Session Authority`.

JWT содержит идентификаторы пользователя, сессии и токена, но актуальность сессии подтверждается Redis.

Пример session state:
```json
{
  "sid": "session-id",
  "user_id": 1,
  "access_jti": "current-access-jti",
  "refresh_jti": "current-refresh-jti",
  "access_exp": 1710000000,
  "refresh_exp": 1710500000
}
```

Для успешной проверки access token должны выполняться условия:
```text
payload.sid == session.sid
payload.sub == session.user_id
payload.jti == session.access_jti
```

---

## 📕 Структура Redis Keys
Проект использует несколько групп Redis-ключей.

### Refresh Whitelist
Хранит активные refresh tokens.  
```text
jwt:white:refresh:{jti}
```

### Blacklist
Хранит отозванные access и refresh tokens.
```text
jwt:black:{jti}
```

### Session Storage
Хранит актуальное состояние пользовательской сессии.
```text
jwt:session:{sid}
```

### User Sessions Index
Хранит список активных session id пользователя.
```text
jwt:user_sessions:{user_id}
```

ℹ️ Подробный жизненный цикл этих ключей описан в [JWT_FLOW](./JWT_FLOW.md).

---

## ⚛️ Атомарность Refresh Rotation
Для атомарности __Refresh rotation__ в проекте используется __Redis transaction pipeline__.

Причины:
- предотвратить _race condition_;
- предотвратить _double refresh_;
- гарантировать единое актуальное состояние _Refresh token_.

В рамках rotation должны быть согласованно обновлены:
- refresh whitelist;
- token blacklist;
- session state.

ℹ️ Подробный пошаговый сценарий описан в [JWT_FLOW](./JWT_FLOW.md).

---

## 🚨 Refresh Token Reuse Detection
Refresh token reuse detection используется для обнаружения повторного использования старого refresh token после rotation.

⚠️ Если старый refresh token используется повторно, session считается потенциально скомпрометированной и отзывается.

В проекте также используется grace-период `JWT_REFRESH_REUSE_GRACE_SECONDS`.  
Он нужен, чтобы технический дубль refresh-запроса сразу после rotation 
не всегда трактовался как полноценный security incident.

ℹ️ Security-обоснование этого поведения описано в [SECURITY_MODEL](./SECURITY_MODEL.md).

---

## ❓ Почему PyJWT, а не SimpleJWT
`PyJWT` выбран намеренно, потому что проекту нужен полный контроль над JWT lifecycle.

Причины выбора:
- полный контроль над __payload__ и __lifecycle__ токенов;
- собственная __Redis session model__;
- собственный __blacklist__ / __whitelist__ логика;
- собственная __refresh rotation__ реализация;
- собственная __reuse detection__ логика;
- возможность дальнейшего выделения в отдельный auth-service.

ℹ️ SimpleJWT хорошо подходит для типовых сценариев, но текущий проект сфокусирован 
на демонстрации собственной управляемой JWT-архитектуры.

---

## ❓ Почему RS256
В проекте, принято решение, использовать `RS256 (RSA SHA-256)` вместо классического `HS256`.

Основные причины: 
- асимметричная криптография;
- _private key_ подписывает токены;
- _public key_ проверяет токены;
- _private key_ остаётся только у auth-компонента;
- _public key_ можно безопасно распространять между сервисами;
- внешние сервисы могут проверять токены, но не могут выпускать их;
- проще переход к микросервисной архитектуре.

ℹ️ Этот выбор важен для потенциального выделения JWT-ядра в отдельный auth-service.

---

## 🛢️ PostgreSQL и Redis

### PostgreSQL
PostgreSQL хранит долговременные данные:
- users;
- groups;
- permissions;
- content.

### Redis
Redis хранит временное auth-состояние:
- active sessions;
- refresh whitelist;
- token blacklist;
- user sessions index.

ℹ️ Такое разделение позволяет не смешивать бизнес-данные и быстро изменяемое состояние аутентификации.

---

## 🗂️ Роли и контент
Для демонстрационной RBAC-модели используются стандартные Django Groups.

Demo-роли:
- `role_1`
- `role_2`

Content API фильтрует объекты по группам текущего пользователя.

ℹ️ Выбор Django Groups сделан потому, что это встроенный механизм Django, 
который подходит для демонстрационного разграничения доступа и не требует отдельной RBAC-модели.

---

## 💡 Возможность выделения auth-service
Архитектура допускает дальнейшее выделение JWT-ядра в отдельный сервис.

Этому способствуют:
- RS256;
- public/private key split;
- Redis-backed session state;
- отдельный JWT service;
- отдельный Redis Token Store;
- явный Auth Service layer.

Потенциальное развитие:
```text
Django auth module
        ↓
Standalone JWT Auth Service
        ↓
Shared auth provider for multiple services
```

⚠️ На текущем этапе это не реализуется намеренно.   
ℹ️ Проект остаётся Django-приложением, но архитектурно не закрывает путь к будущему выделению auth-ядра.

---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [JWT_FLOW](./JWT_FLOW.md) ── Жизненный цикл токенов.
- [SECURITY_MODEL](./SECURITY_MODEL.md) ── Модель безопасности.
- [DEVELOPMENT](./DEVELOPMENT.md) ── Локальный запуск и команды разработки.
- [API_EXAMPLES](./API_EXAMPLES.md) ── Примеры API-запросов.
- [BRUNO](./BRUNO.md) ── Коллекция Bruno для воспроизведения Auth, Content и Security сценариев.

---

## 📌 Итог
DjangoJWT — это не простой stateless JWT-пример.

Проект реализует управляемую JWT-session архитектуру:
- JWT передаёт claims
- Redis подтверждает актуальность session
- Blacklist отзывает токены
- Whitelist контролирует refresh lifecycle
- Rotation снижает replay risk
- Reuse detection выявляет подозрительное использование refresh token