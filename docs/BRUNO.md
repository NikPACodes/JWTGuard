# 🐶 DjangoJWT ── Bruno Collection

## 🎯 Назначение документа
Этот документ описывает структуру и использование коллекции __Bruno__, хранящейся в репозитории DjangoJWT
как вспомогательный инструмент ручного тестирования API.

---

## Оглавление
- [DjangoJWT — Bruno Collection](#-djangojwt--bruno-collection)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [Bruno Collection](#-bruno-collection)
  - [Почему Bruno](#-почему-bruno)
  - [Структура коллекции](#-структура-коллекции)
  - [Установка Bruno](#-установка-bruno)
    - [Bruno Desktop](#bruno-desktop)
    - [Bruno CLI](#bruno-cli)
  - [Настройка окружения](#-настройка-окружения)
    - [️Подготовка](#подготовка)
    - [Environment](#environment)
  - [Bruno Flows](#-bruno-flows)
    - [Auth Flow](#auth-flow)
    - [Content Flow](#content-flow)
    - [Security Flow](#security-flow)
  - [Запуск](#-запуск)
    - [Через Bruno Desktop](#через-bruno-desktop)
    - [Через Bruno CLI](#через-bruno-cli)
  - [Связанные документы](#-связанные-документы)

---

## 🐶 Bruno Collection
Проект DjangoJWT включает коллекцию __Bruno__ для ручного тестирования API и 
демонстрации основных сценариев работы системы аутентификации и авторизации.

__Bruno__ используется как дополнение к существующим механизмам контроля качества проекта:
- __Pytest__ ── автоматические тесты бизнес-логики и security-сценариев;
- __GitHub Actions__ ── автоматическая проверка проекта в CI;
- __Swagger UI__ ── интерактивное исследование API;
- __Bruno__ ── воспроизведение готовых пользовательских сценариев через HTTP-запросы.

Коллекция включает сценарии для проверки:
- Authentication Flow;
- Content Access Flow;
- Refresh Token Rotation;
- Refresh Token Reuse Detection;
- Session Revocation;
- Logout All Sessions.

ℹ️ Bruno не заменяет автоматические тесты и используется как дополнительный инструмент демонстрации и ручной проверки API.

---

## ❓ Почему Bruno
Для проекта был выбран __Bruno__ вместо __Postman__ по следующим причинам:
- коллекции хранятся в обычных текстовых файлах;
- коллекции удобно версионировать в Git;
- отсутствует зависимость от облачных сервисов;
- поддерживает хранение коллекций рядом с исходным кодом проекта, как часть репозитория;
- поддерживается запуск как через графический интерфейс, так и через CLI.

---

## 🏗️ Структура коллекции
```text
bruno/
└── DjangoJWT/
    ├── bruno.json
    ├── environments/
    │   └── local.bru
    │
    ├── Auth/
    │   ├── 01 Health
    │   ├── 02 Register Role 1
    │   ├── 03 Login Role 1
    │   ├── 04 Profile
    │   ├── 05 Refresh
    │   ├── 06 Logout
    │   └── 07 Profile After Logout
    │
    ├── Content/
    │   ├── 01 Content Health
    │   ├── 02 Login For Content Test
    │   ├── 03 Available Content
    │   └── 04 Content Detail
    │
    └── Security/
        ├── 01 Login For Reuse Test
        ├── 02 Refresh First Time
        ├── 03 Reuse Old Refresh Token
        ├── 04 Profile After Reuse
        ├── 05 Login Again
        ├── 06 Logout All
        └── 07 Profile After Logout All
```

---
## 🛠️ Установка Bruno

### Bruno Desktop
Скачать __Bruno__ можно с официального сайта.

Либо установить через Snap:
```bash
sudo snap install bruno
```


### Bruno CLI
Для запуска коллекций из терминала:
```bash
npm install -g @usebruno/cli
```

Проверка установки:
```bash
bru --version
```

---

## ️️🛠️ Настройка окружения
### ️Подготовка
Перед запуском Bruno необходимо запустить проект:
```bash
make up-d
make migrate
make demo
```

После запуска API должен быть доступен по адресу:
```text
http://localhost:8000
```

### Environment
Коллекция использует файл:
```text
bruno/DjangoJWT/environments/local.bru
```

Основные переменные:
```dotenv
  base_url: http://localhost:8000
  role1_email: role1@example.com
  role1_username: role1
  role1_password: StrongPass123!
  role2_email: role2@example.com
  role2_username: role2
  role2_password: StrongPass123!
  access_token:
  refresh_token:
  old_refresh_token:
  wait_grace_ms: 6000
```

ℹ️ Токены заполняются автоматически во время выполнения запросов.

---

## 🔁 Bruno Flows

### Auth Flow
Папка __Auth__ демонстрирует базовый жизненный цикл JWT-аутентификации.

Сценарий:
```text
Register
↓
Login
↓
Profile
↓
Refresh
↓
Logout
↓
Profile After Logout
```

Проверяемые возможности:
- регистрация пользователя;
- выдача JWT-токенов;
- получение профиля;
- refresh rotation;
- отзыв сессии;
- блокировка доступа после logout.


### Content Flow

Папка __Content__ демонстрирует доступ к защищённым данным.

Сценарий:
```text
Login
↓
Content List
↓
Content Detail
```

Проверяемые возможности:
- JWT-аутентификация;
- доступ к защищённым API;
- работа RBAC через Django Groups;
- фильтрация контента по ролям.


### Security Flow
Папка __Security__ демонстрирует расширенные механизмы защиты JWT-сессий.

Сценарий:
```text
Login
↓
Refresh
↓
Reuse Old Refresh Token
↓
Session Revoked
↓
Access Rejected
↓
Login Again
↓
Logout All
↓
Profile After Logout All
```

Проверяемые возможности:
- Refresh Token Rotation;
- Refresh Token Reuse Detection;
- Session Revocation;
- Logout All Sessions.

ℹ️ Данный сценарий является одним из ключевых элементов архитектуры DjangoJWT.

---

## ▶️ Запуск
### Через Bruno Desktop
Запустить __Bruno__.

Выбрать:
```text
Open Collection
```

Указать путь:
```text
bruno/DjangoJWT
```

Выбрать окружение:
```text
local
```

ℹ️ После этого можно запускать запросы вручную.


### Через Bruno CLI
Полная коллекция:
```bash
make bruno
```

Только аутентификация:
```bash
make bruno-auth
```

Только контент:
```bash
make bruno-content
```

Только security-сценарии:
```bash
make bruno-security
```

---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [ARCHITECTURE](./ARCHITECTURE.md) ── Архитектура проекта.
- [JWT_FLOW](./JWT_FLOW.md) ── Жизненный цикл токенов.
- [SECURITY_MODEL](./SECURITY_MODEL.md) ── Модель безопасности.
- [DEVELOPMENT](./DEVELOPMENT.md) ── Локальный запуск и команды разработки.
- [API_EXAMPLES](./API_EXAMPLES.md) ── Примеры API-запросов.