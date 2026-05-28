# 🔐 DjangoJWT — управляемая JWT-аутентификация на Django, PyJWT и Redis

**DjangoJWT** — учебно-инженерный backend-проект на Django REST Framework, 
реализующий управляемую JWT-аутентификацию с использованием `PyJWT`, `RS256`, `Redis` и `PostgreSQL`.

---

## Оглавление
- [DjangoJWT — управляемая JWT-аутентификация на Django, PyJWT и Redis](#-djangojwt--управляемая-jwt-аутентификация-на-django-pyjwt-и-redis)
  - [Оглавление](#оглавление)
  - [Идея проекта](#-идея-проекта)
  - [Ключевые возможности](#-ключевые-возможности)
  - [Стек](#-стек)
  - [Быстрый старт](#-быстрый-старт)
  - [RSA-ключи](#-rsa-ключи)
  - [Makefile-команды](#-makefile-команды)
  - [API endpoints](#-api-endpoints)
    - [Auth](#auth)
    - [Content](#content)
    - [API documentation](#api-documentation)
  - [Демонстрационные роли и контент](#-демонстрационные-роли-и-контент)
  - [Тесты](#-тесты)
  - [Почему не используется access whitelist](#-почему-не-используется-access-whitelist)
  - [Ограничения](#-ограничения)
  - [Документация и правила проекта](#-документация-и-правила-проекта)
    - [Лицензия](#-лицензия)
    - [Вклад в проект](#-вклад-в-проект)
    - [Развертывание проекта](#-развертывание-проекта)
    - [Архитектура](#-архитектура)
  - [Перспективы развития](#-перспективы-развития)

---

## 🎯 Идея проекта

Классический JWT часто используется как полностью stateless credential.

Такой подход прост, но ограничивает возможности управления сессиями:
- сложно выполнить logout до истечения токена;
- сложно отозвать конкретную сессию;
- сложно обнаружить повторное использование refresh token;
- сложно централизованно управлять активными пользовательскими сессиями.

В этом проекте используется __гибридный подход__:
```text
JWT = переносимый authentication credential
Redis = источник актуального состояния сессии
```

ℹ️ JWT остаётся удобным форматом передачи identity-данных, но окончательное решение о валидности сессии принимается с учётом состояния в Redis.

---

## ⚙️ Ключевые возможности

- собственная генерация и проверка JWT через `PyJWT`;
- асимметричная подпись токенов через `RS256`;
- Redis-backed session state;
- пара токенов access / refresh;
- refresh token whitelist;
- access / refresh blacklist;
- atomic refresh rotation;
- refresh token reuse detection;
- регистрация пользователя;
- login по email/password;
- logout текущей сессии;
- logout всех сессий пользователя;
- демонстрационная ролевая модель через Django Groups;
- защищённый content API;
- Docker-окружение для локального запуска;
- тесты основных auth-flow сценариев.

---

## 🏗️ Стек

- Python 3.12
- Django
- Django REST Framework
- PyJWT
- Redis
- PostgreSQL
- Docker / Docker Compose
- Pytest
- drf-spectacular

---

## ▶️ Быстрый старт

Для быстрого запуска выполните следующие команды:
```bash
git clone https://github.com/NikPACodes/DjangoJWT.git
cd DjangoJWT
cp .env.example .env.dev
make keys
make build
make up-d
make migrate
make demo
```
После этого проект будет готов к локальной проверке.

ℹ️ Подробная инструкция — [DEVELOPMENT](./docs/DEVELOPMENT.md)

---

## 🔑 RSA-ключи

Проект использует `RS256`, поэтому для работы JWT нужны _private_/_public_ RSA-ключи.

Сгенерировать ключи можно командой:
```bash
make keys
```

Проверить соответствие _private_/_public_ key:
```bash
make verify-keys
```

_Private key_ используется для подписи токенов.  
_Public key_ используется для проверки токенов.

⚠️ ️️Файлы ключей не должны попадать в Git.

---

## 📜 Makefile-команды

Основные команды проекта:
```bash
make build            # собрать Docker-образы
make up-d             # запустить контейнеры в background
make down             # остановить контейнеры
make logs             # логи app-контейнера
make ps               # статус контейнеров
make migrate          # применить миграции
make demo             # создать demo-данные
make tests            # запустить тесты
make check            # выполнить django check
make keys             # сгенерировать RSA-ключи
...
```

ℹ️ Полный список команд с пояснениями — [DEVELOPMENT](./docs/DEVELOPMENT.md)

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
GET /api/docs/swagger/
GET /api/docs/redoc/
```

ℹ️ Примеры запросов — [API_EXAMPLES](./docs/API_EXAMPLES.md)

---

## 💡 Демонстрационные роли и контент

Проект использует стандартные Django Groups для демонстрационной RBAC-модели.

Команда создания тестовых ролей и демонстрационного контента:
```bash
make demo
```

ℹ️ Content API возвращает только тот контент, который доступен группам текущего пользователя.

---

## ⚡ Тесты

Запуск тестов:
```bash
make tests
```

Тестами покрываются основные сценарии:
- login;
- registration;
- access token validation;
- refresh rotation;
- atomic refresh rotation;
- refresh token reuse detection;
- logout;
- logout all sessions;
- token store;
- role-based content access.

---

## ❓ Почему не используется access whitelist

Проект намеренно не хранит access token в whitelist.

Access token:
- короткоживущий;
- проверяется по RS256-подписи;
- проверяется по expiration;
- проверяется по blacklist;
- проверяется через Redis session state;
- должен соответствовать `session.access_jti`.

Такой подход позволяет сохранить управляемость сессий без необходимости хранить каждый access token в отдельном whitelist.

Подробное объяснение находится в [ARCHITECTURE](./docs/ARCHITECTURE.md) и [SECURITY_MODEL](./docs/SECURITY_MODEL.md).

---

## 🚧 Ограничения

Проект является учебно-инженерным примером и не претендует на готовую production-auth платформу.

Для production-использования дополнительно потребуются:
- HTTPS;
- защищённое хранение private key;
- ротация RSA ключей;
- rate limiting;
- audit logging security-событий;
- мониторинг Redis;
- защита Redis от внешнего доступа;
- alerting при refresh token reuse detection;
- политика управления security incidents.

---

## 📚 Документация и правила проекта

### 📄 Лицензия
Условия использования и распространения проекта — [LICENSE](./LICENSE)

### 🤝 Вклад в проект
Как сообщать об ошибках и уязвимостях — [CONTRIBUTING](./CONTRIBUTING.md)

### 🛠 Развертывание проекта
Локальный запуск, Docker, Makefile-команды и тесты ── [DEVELOPMENT](./docs/DEVELOPMENT.m

### 🏗️ Архитектура
Описание общей архитектуры проекта — [ARCHITECTURE](./docs/ARCHITECTURE.md)  
Жизненный цикл токенов и auth-flow — [JWT_FLOW](./docs/JWT_FLOW.md)  
Модель безопасности, угрозы и ограничения — [SECURITY_MODEL](./docs/SECURITY_MODEL.md)  
Примеры API-запросов — [API_EXAMPLES](./docs/API_EXAMPLES.md)

---

## 🚀 Перспективы развития

Проект считается завершённым в рамках текущей цели: 
показать управляемую JWT-аутентификацию на `Django`, `DRF`, `PyJWT`, `RS256` и `Redis`.

На основе проекта готовится инженерная статья о реализации продвинутого JWT-flow:
- refresh rotation;
- blacklist / whitelist;
- refresh token reuse detection;
- atomic token rotation.

Архитектура проекта допускает дальнейшее развитие JWT-ядра в независимый auth-service, 
но это будет реализовываться в рамках отдельного проекта.

Дополнительно может быть добавлена Bruno collection для локального API-тестирования.