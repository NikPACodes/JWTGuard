# 🛠️ DjangoJWT — Development Guide

## 🎯 Назначение документа
Этот документ описывает локальный запуск проекта, работу с Docker-окружением,
переменными окружения, RSA-ключами, Makefile-командами и тестами.

---

## Оглавление
- [DjangoJWT — Development Guide](#-djangojwt--development-guide)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [Требования](#-требования)
  - [Быстрый старт](#-быстрый-старт)
    - [1. Клонировать репозиторий](#1-клонировать-репозиторий)
    - [2. Создать .env](#2-создать-env)
    - [3. Сгенерировать RSA-ключи](#3-сгенерировать-rsa-ключи)
    - [4. Собрать и запустить контейнеры](#4-собрать-и-запустить-контейнеры)
    - [5. Применить миграции](#5-применить-миграции)
    - [6. Создать демонстрационные данные](#6-создать-демонстрационные-данные)
  - [Переменные окружения](#-переменные-окружения)
  - [RSA-ключи](#-rsa-ключи)
  - [Docker Compose](#-docker-compose)
    - [App](#-app)
    - [Postgres](#-postgres)
    - [Redis](#-redis)
  - [Makefile-команды](#-makefile-команды)
    - [Docker](#docker)
    - [Django](#django)
    - [Demo data](#demo-data)
    - [JWT keys](#jwt-keys)
    - [Clean](#clean)
    - [Schema](#schema)
  - [Тесты](#-тесты)
  - [Проверка API-документации](#-проверка-api-документации)
  - [Типичный локальный workflow](#-типичный-локальный-workflow)
  - [Возможные проблемы](#-возможные-проблемы)
    - [Ошибка: private/public key не найден](#ошибка-privatepublic-key-не-найден)
    - [Ошибка: порт уже занят](#ошибка-порт-уже-занят)
    - [Ошибка подключения к PostgreSQL](#ошибка-подключения-к-postgresql)
    - [Ошибка подключения к Redis](#ошибка-подключения-к-redis)
    - [Роль при регистрации не найдена](#роль-при-регистрации-не-найдена)
  - [Связанные документы](#-связанные-документы)

---

## 🚧 Требования

Для локального запуска потребуется:
- Docker;
- Docker Compose;
- Make;
- OpenSSL.

Проект рассчитан на запуск через Docker Compose. 
Локальная установка Python-зависимостей на host-машину не требуется.

---

## ▶️ Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/NikPACodes/DjangoJWT.git
cd DjangoJWT
```


### 2. Создать `.env`

```bash
cp .env.example .env.dev
```
ℹ️ Проверь значения переменных окружения и при необходимости измени их под локальное окружение.


### 3. Сгенерировать RSA-ключи

```bash
make keys
```

Будут созданы:
```text
certs/jwt_private.pem
certs/jwt_public.pem
```
⚠️ ️️Файлы ключей не должны попадать в Git.


### 4. Собрать и запустить контейнеры

```bash
make build
make up-d
```


### 5. Применить миграции

```bash
make migrate
```


### 6. Создать демонстрационные данные

```bash
make demo
```

ℹ️ Команда создаёт группы `role_1`, `role_2` и демонстрационный контент.

️⚠️ ️ Demo-пользователи этой командой не создаются.
Пользователя можно создать через `/api/auth/register/` или через Django `admin`.

---


## 🛠️ Переменные окружения

Пример переменных находится в `.env.example`.

Для локальной разработки используется файл `.env.dev`.

Основные переменные:
```dotenv
DJANGO_SETTINGS_MODULE='config.settings.dev'
DJANGO_SECRET_KEY='super_secret_key'
DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'

POSTGRES_DB='djangojwt'
POSTGRES_USER='djangojwt'
POSTGRES_PASSWORD='djangojwt'
POSTGRES_HOST='localhost'
POSTGRES_PORT=5432

REDIS_URL=redis://localhost:6379/0

JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH='certs/jwt_private.pem'
JWT_PUBLIC_KEY_PATH='certs/jwt_public.pem'
JWT_ISSUER='djangojwt'
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=604800
JWT_REFRESH_REUSE_GRACE_SECONDS=5
```

ℹ️ В Docker Compose часть параметров переопределяются под контейнерное окружение:
```dotenv
POSTGRES_HOST=postgres
REDIS_URL=redis://redis:6379/0
JWT_PRIVATE_KEY_PATH=/app/certs/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/app/certs/jwt_public.pem
```

---

## 🔑 RSA-ключи

Проект использует `RS256`, поэтому для работы JWT нужны private/public RSA-ключи.

Сгенерировать ключи можно командой:
```bash
make keys
```

Проверить соответствие private/public key:
```bash
make verify-keys
```

Private key используется для подписи токенов.
Public key используется для проверки токенов.

⚠️ ️️Файлы ключей не должны попадать в Git.

---

## 🐋 Docker Compose

Проект запускается через Docker Compose.

Основные сервисы:
- __App__
- __Postgres__
- __Redis__


### 🧩 App
Django-приложение.

Отвечает за:
- HTTP API;
- JWT auth-flow;
- работу с PostgreSQL;
- работу с Redis;
- выполнение management commands;
- запуск тестов.


### 🛢️ Postgres
Основная relational database.

Postgres хранит:
- пользователей;
- групп; 
- permissions;
- content.


### 🗃️ Redis
Используется как хранилище runtime-состояния аутентификации: refresh-сессий, JTI и признаков отзыва токенов.

Redis хранит:
- активные пользовательские сессии;
- whitelist refresh-токенов;
- blacklist отозванных токенов;
- индекс сессий пользователя.

---

## 📜 Makefile-команды

### Docker
```bash
make build      # собрать Docker-образы
make up         # запустить контейнеры в foreground
make up-d       # запустить контейнеры в background
make down       # остановить контейнеры
make restart    # пересобрать и перезапустить контейнеры
make ps         # показать статус контейнеров
make logs       # показать логи app-контейнера
```


### Django
```bash
make bash             # открыть bash внутри app-контейнера
make shell            # открыть Django shell
make migrate          # применить миграции
make makemigrations   # создать миграции
make createsuperuser  # создать superuser
make check            # выполнить django check
```


### Demo data
```bash
make demo  # создаёт demo-группы и demo-контент
```


### Tests
```bash
make tests  # запускает тесты проекта
```


### JWT keys
```bash
make keys         # генерация RSA-ключей
make verify-keys  # проверка RSA-ключей
```


### Clean
```bash
make clean  # останавливает контейнеры и удаляет Docker volumes
```

⚠️ ️️Внимание: `make clean` удаляет данные PostgreSQL, потому что выполняет `docker compose down -v`.


### Schema
```bash
make schema  # получение OpenAPI schema
```

---

## ⚡ Тесты

Запуск тестов:
```bash
make tests
```

Тестами покрываются основные сценарии:
- registration;
- login;
- access token validation;
- refresh rotation;
- atomic refresh rotation;
- refresh token reuse detection;
- logout;
- logout all sessions;
- Redis token store;
- role-based content access.

---

## 📑 Проверка API-документации

После запуска проекта доступны:
```text
GET /api/schema/
GET /api/schema/swagger/
GET /api/schema/redoc/
```

ℹ️ Swagger UI можно использовать для ручной проверки endpoints.

---

## 🔄 Типичный локальный workflow

Полный цикл локального запуска:
```bash
cp .env.example .env.dev
make keys
make build
make up-d
make migrate
make demo
make tests
```

Остановить окружение:
```bash
make down
```

Полностью очистить окружение вместе с volume-данными:
```bash
make clean
```

---


## 🆘 Возможные проблемы

### Ошибка: private/public key не найден
Проверь, что ключи сгенерированы:
```bash
make keys
```

И что в `.env.dev` указаны корректные пути:
```dotenv
JWT_PRIVATE_KEY_PATH=certs/jwt_private.pem
JWT_PUBLIC_KEY_PATH=certs/jwt_public.pem
```

Для Docker-окружения пути могут быть переопределены как:
```dotenv
JWT_PRIVATE_KEY_PATH=/app/certs/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/app/certs/jwt_public.pem
```

Также можно проверить соответствие private/public key:
```bash
make verify-keys
```


### Ошибка: порт уже занят

При запуске Docker Compose может возникнуть ошибка вида:
```text
Bind for 0.0.0.0:8000 failed: port is already allocated
```
или аналогичная ошибка для портов PostgreSQL/Redis.

Чаще всего конфликтуют порты:
- `8000` — Django application
- `5432` — PostgreSQL
- `6379` — Redis

Проверить, занят ли порт:
```bash
ss -ltnp | grep ':8000'
ss -ltnp | grep ':5432'
ss -ltnp | grep ':6379'
```

Альтернативно:
```bash
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379
```

Возможные решения:
1. Остановить локальный сервис, который занимает порт.

2. Изменить host-порт в `docker-compose.yml`.

3. Использовать уже запущенный локальный PostgreSQL/Redis, если проект запускается не полностью через Docker.

Пример замены host-портов в docker-compose.yml:
```yaml
services:
  app:
    ports:
      - "8001:8000"

  postgres:
    ports:
      - "5433:5432"

  redis:
    ports:
      - "6380:6379"
```

После этого приложение будет доступно на хосте по адресу `http://localhost:8001`.  
PostgreSQL с хоста будет доступен на порту `5433`.  
Redis с хоста будет доступен на порту `6380`.  

⚠️ __Важно:__ если Django-приложение запускается внутри Docker Compose, 
то контейнеры продолжают общаться между собой по внутренним адресам:
```dotenv
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
```

Менять эти значения нужно только если Django запускается локально вне Docker 
и подключается к сервисам через проброшенные host-порты.


### Ошибка подключения к PostgreSQL

Проверь, что контейнеры запущены:
```bash
make ps
```

Посмотри логи:
```bash
make logs
```

Если PostgreSQL запущен локально на машине и занимает порт `5432`, 
Docker Compose может не стартовать с пробросом `5432:5432`.

Проверь порт:
```bash
ss -ltnp | grep ':5432'
```

Варианты решения:
1. Остановить локальный PostgreSQL.

2. Изменить host-порт PostgreSQL в `docker-compose.yml`, например:
    ```yaml
    postgres:
      ports:
        - "5433:5432"
    ```

3. Если Django запускается вне Docker, указать в `.env.dev` новый порт:
    ```dotenv
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5433
    ```

Если база была повреждена или нужна полная очистка:
```bash
make clean
make up-d
make migrate
make demo
```


### Ошибка подключения к Redis

Проверь REDIS_URL в `.env.dev`.

Для локального запуска без Docker обычно используется:
```dotenv
REDIS_URL=redis://localhost:6379/0
```

Для Docker Compose внутри Docker-сети:
```dotenv
REDIS_URL=redis://redis:6379/0
```

Если локальный Redis уже занимает порт `6379`, 
Docker Compose может не стартовать с пробросом `6379:6379`.

Проверь порт:
```bash
ss -ltnp | grep ':6379'
```

Варианты решения:
1. Остановить локальный Redis.

2. Изменить host-порт Redis в `docker-compose.yml`, например:
    ```yaml
    redis:
      ports:
        - "6380:6379"
   ```
   
3. Если Django запускается вне Docker, указать в `.env.dev` новый порт:
    ```dotenv
    REDIS_URL=redis://localhost:6380/0
    ```

Если Django запускается внутри Docker Compose, внутренний адрес Redis обычно остаётся прежним:
```dotenv
REDIS_URL=redis://redis:6379/0
```


### Роль при регистрации не найдена

Перед регистрацией пользователя с ролью `role_1` или `role_2` выполни:
```bash
make demo
```
Команда создаёт необходимые Django Groups.

Если ошибка сохраняется, проверь список групп через Django shell:
```bash
make shell
```

```python
from django.contrib.auth.models import Group

Group.objects.values_list("name", flat=True)
```
---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [ARCHITECTURE](./ARCHITECTURE.md) ── Архитектура проекта.
- [JWT_FLOW](./JWT_FLOW.md) ── Жизненный цикл токенов.
- [SECURITY_MODEL](./SECURITY_MODEL.md) ── Модель безопасности.
- [API_EXAMPLES](./API_EXAMPLES.md) ── Примеры API-запросов.