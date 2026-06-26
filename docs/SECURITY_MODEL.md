# 🛡️ JWTGuard — Security Model

## 🎯 Назначение документа
Этот документ описывает модель безопасности проекта JWTGuard:
- какие угрозы учитываются;
- какие гарантии даёт текущая реализация;
- как защищаются Access и Refresh tokens;
- какую роль выполняет Redis;
- какие ограничения остаются в текущей версии.

---

## Оглавление

- [JWTGuard — Security Model](#-jwtguard--security-model)
  - [Назначение документа](#-назначение-документа)
  - [Оглавление](#оглавление)
  - [Общая модель безопасности](#-общая-модель-безопасности)
  - [Цели Security model](#-цели-security-model)
  - [Threat Model](#-threat-model)
  - [Access Token Security](#-access-token-security)
    - [Почему Access token короткоживущий](#-почему-access-token-короткоживущий)
    - [Почему access whitelist не используется](#-почему-access-whitelist-не-используется)
    - [Blacklist Revoke для Access token](#-blacklist-revoke-для-access-token)
  - [Refresh Token Security](#-refresh-token-security)
    - [Refresh Whitelist](#refresh-whitelist)
    - [Refresh Blacklist](#refresh-blacklist)
  - [Refresh Rotation](#-refresh-rotation)
  - [Atomic Rotation](#-atomic-rotation)
  - [Refresh Token Reuse Detection](#-refresh-token-reuse-detection)
    - [Grace-период](#grace-период)
    - [Реакция на reuse](#реакция-на-reuse)
  - [Logout / Revoke Session](#-logout--revoke-session)
  - [Logout All Sessions](#-logout-all-sessions)
  - [Redis Session Authority](#-redis-session-authority)
    - [Redis недоступен](#redis-недоступен)
    - [Redis скомпрометирован](#redis-скомпрометирован)
  - [RSA-ключи](#-rsa-ключи)
  - [HTTPS](#-https)
  - [Кража токенов на стороне клиента](#-кража-токенов-на-стороне-клиента)
  - [Token Storage](#-token-storage)
  - [Ограничения](#-ограничения)
  - [Production Hardening](#-production-hardening)
  - [Итоговая модель](#-итоговая-модель)
  - [Связанные документы](#-связанные-документы)

---

## 🎯 Общая модель безопасности
JWTGuard использует управляемую JWT-аутентификацию с Redis-backed session state.
Ключевая идея:
```text
valid JWT + active Redis session = authenticated request
```

JWT подтверждает:
- подпись токена;
- срок действия;
- тип токена;
- claims пользователя и сессии.

Redis подтверждает:
- что сессия существует;
- что токен соответствует текущему состоянию сессии;
- что Refresh token активен;
- что токен не был отозван.

⚠️ Валидный JWT сам по себе не является достаточным основанием для доступа.

---

## 🎯 Цели Security model
Основные цели security model:
- ограничить ущерб при компрометации Access token;
- строго контролировать жизненный цикл Refresh token;
- поддержать logout до истечения JWT;
- предотвратить повторное использование старого Refresh token;
- защититься от double refresh / race condition;
- хранить актуальное состояние сессии в Redis;
- разделить persistent data и security session state;
- подготовить архитектуру к возможному выделению auth-ядра в отдельный сервис.

---

## 🚨 Threat Model
Система проектируется для снижения рисков:
- кражи Access token;
- кражи Refresh token;
- replay attacks;
- использования токенов после logout;
- использования старого Refresh token после rotation;
- появления нескольких активных Refresh tokens для одной session;
- сохранения session после revoke;
- обхода logout через ранее выданный JWT;
- неконсистентного состояния при параллельных refresh-запросах.

⚠️ Не рассматриваются как полностью решённые в рамках проекта:
- компрометация устройства пользователя;
- XSS на стороне клиента;
- компрометация Redis;
- компрометация private key;
- отсутствие HTTPS;
- brute-force атаки на login endpoint;
- полноценный OAuth2 / OIDC provider flow.

---

## 🔐 Access Token Security
Access token используется для доступа к защищённым API endpoints.

Он считается менее ценным, чем Refresh token, потому что:
- имеет короткий TTL;
- не используется для получения долгосрочного доступа напрямую;
- может быть отозван через blacklist;
- должен соответствовать активной Redis session.


### ❓ Почему Access token короткоживущий
Короткий TTL снижает ущерб при краже Access token.

Даже если Access token был украден, атакующий ограничен:
- временем жизни токена;
- проверкой Blacklist;
- проверкой Redis session state;
- возможностью session revoke.


### ❓ Почему access whitelist не используется
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


### ❓ Blacklist Revoke для Access token
Access token может быть добавлен в _blacklist_ до истечения срока жизни.

Это используется при:
- logout;
- logout all sessions;
- refresh rotation;
- session revoke;
- refresh token reuse detection.

⚠️ Если Access token находится в _blacklist_, он считается недействительным независимо от `exp`.

---

## 🔑 Refresh Token Security
Refresh token является главным долгоживущим credential системы.

Причины:
- живёт дольше Access token;
- используется для получения новой пары токенов;
- при компрометации может дать атакующему долгосрочный доступ;
- требует строгого контроля через Redis whitelist и session state.

Refresh token считается активным, если:
1. токен успешно декодирован;
2. `RS256` signature валиден;
3. `exp` не истёк;
4. `type == refresh`;
5. `jti` отсутствует в blacklist;
6. `jti` присутствует в Refresh whitelist;
7. Redis session существует;
8. `payload.jti == session.refresh_jti`.


### Refresh Whitelist
Refresh token хранится в Redis whitelist.

Whitelist позволяет:
- проверить, что Refresh token всё ещё активен;
- отозвать Refresh token до expiration;
- связать Refresh token с конкретной session;
- реализовать logout;
- реализовать logout all sessions;
- обнаружить повторное использование старого Refresh token.

⚠️ Если Refresh token отсутствует в whitelist, он не может использоваться для refresh rotation.


### Refresh Blacklist
Refresh token добавляется в Blacklist после:
- refresh rotation;
- logout;
- logout all sessions;
- session revoke;
- refresh token reuse detection.

⚠️ Повторное использование blacklisted Refresh token является подозрительным событием и может привести к session revoke.

---

## ♻️ Refresh Rotation
Refresh rotation снижает риск replay attack.

При каждом успешном refresh:
1. старый Refresh token удаляется из whitelist;
2. старый Refresh token добавляется в blacklist;
3. старый Access token добавляется в blacklist;
4. генерируется новый Access token;
5. генерируется новый Refresh token;
6. новый Refresh token добавляется в whitelist;
7. Redis session обновляется новыми `access_jti` и `refresh_jti`;
8. клиент получает новую пару токенов.

ℹ️ Таким образом, Refresh token становится одноразовым в рамках успешной rotation.

---

## ⚛️ Atomic Rotation
Refresh rotation выполняется атомарно через Redis transaction pipeline.

ℹ️ Это защищает от ситуации, когда два параллельных запроса используют один и тот же Refresh token.

Без атомарности возможен риск:
```text
один старый Refresh token
↓
два параллельных refresh-запроса
↓
параллельное создание двух новых пар токенов 
↓
неконсистентное состояние session
```

Атомарность нужна для консистентности:
- Refresh whitelist;
- Blacklist;
- Redis session state.

---

## 🚨 Refresh Token Reuse Detection
Refresh Token Reuse Detection предназначен для обнаружения повторного использования уже отозванного Refresh token.

Reuse может означать:
- кражу Refresh token;
- replay attempt;
- ошибку клиента;
- повторную отправку старого запроса;
- некорректное сохранение новой пары токенов на клиенте.

ℹ️ Backend __НЕ МОЖЕТ__ надёжно отличить ошибку клиента от атаки, поэтому повторное использование старого Refresh token
рассматривается как security event.


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

ℹ️ Цель реакции — остановить потенциально скомпрометированную session.

---

## 🚪 Logout / Revoke Session
Logout должен завершать текущую session до истечения JWT.

При logout:
- Access token добавляется в blacklist;
- Refresh token добавляется в blacklist;
- Refresh token удаляется из whitelist;
- Redis session удаляется;
- `sid` удаляется из индекса сессий пользователя.

После logout:
- старый Access token не должен проходить protected endpoints;
- старый Refresh token не должен использоваться для refresh;
- Redis session больше не должна существовать.

---

## 🚪 Logout All Sessions
Logout all завершает все активные сессии пользователя.

Для каждой session:
- Access token добавляется в Blacklist;
- Refresh token добавляется в Blacklist;
- Refresh token удаляется из Whitelist;
- Redis session удаляется.

ℹ️ После logout all ни одна старая пара токенов пользователя не должна оставаться активной.

---

## 🗃️ Redis Session Authority
Redis является источником актуального состояния session.

Redis хранит:
- active sessions;
- Refresh Whitelist;
- token Blacklist;
- user sessions index.

⚠️ Если Redis session отсутствует, Access token отклоняется.

Это означает:
```text
JWT может быть валиден криптографически,
но невалиден с точки зрения session state.
```


### Redis недоступен
Redis является обязательной зависимостью auth-flow.

Если Redis недоступен, backend не может надёжно проверить:
- активность session;
- Blacklist;
- Refresh Whitelist;
- соответствие `access_jti` / `refresh_jti`.

⚠️ Безопасное поведение в такой ситуации — отказать в доступе.


### Redis скомпрометирован
Компрометация Redis является критическим security incident.

Возможные последствия:
- подмена session state;
- обход revoke;
- удаление Blacklist entries;
- добавление Refresh token в Whitelist;
- несанкционированное завершение session; 
- нарушение целостности auth-flow.

⚠️ Redis должен быть:
- недоступен из публичной сети;
- изолирован внутри инфраструктуры;
- защищён паролем;
- доступен только backend-приложению;
- настроен с корректной политикой хранения данных.

---

## 🔑 RSA-ключи
Проект использует `RS256`.

_Private key_ используется для подписи токенов.  
_Public key_ используется для проверки токенов.

⚠️ Правила безопасности:
- private key не должен попадать в Git;
- private key не должен встраиваться в публичный Docker image;
- private key должен передаваться через защищённый механизм конфигурации;
- public key может использоваться сервисами для проверки токенов;
- при компрометации private key требуется rotation ключей.

---

## 🌐 HTTPS
JWT-токены должны передаваться только через HTTPS.

Передача JWT через HTTP создаёт риск перехвата:
- Access token;
- Refresh token;
- credentials пользователя.

⚠️ В production-среде HTTPS __обязателен__.

---

## 👤 Кража токенов на стороне клиента
Backend не может полностью защитить токены от кражи на стороне клиента.

Возможные причины:
- XSS;
- вредоносные расширения браузера;
- компрометация local storage;
- вредоносное ПО;
- утечка токенов через клиентские логи.

Backend снижает ущерб через:
- короткий TTL Access token;
- Refresh rotation;
- Blacklist;
- Redis session validation;
- Refresh token reuse detection;
- session revoke.

---

## 🗄️ Token Storage
Проект не навязывает конкретный способ хранения токенов на клиенте.

Возможные варианты:
- httpOnly Secure cookies;
- in-memory storage;
- secure storage в mobile-приложениях.

⚠️ Хранение Refresh token в LocalStorage повышает риски при XSS.

ℹ️ Для production-сценариев предпочтительно использовать более защищённые механизмы хранения токенов.

---

## 🚧 Ограничения
Проект является учебно-инженерным примером и не претендует на готовую production-auth платформу.

Ограничения:
- нет полноценного audit log security-событий;
- нет rate limiting auth endpoints;
- нет brute-force protection;
- нет token binding к устройству;
- нет device/session metadata;
- нет RSA key rotation flow;
- нет централизованного incident management;
- нет отдельного OAuth2 / OIDC provider layer;
- Redis является обязательной зависимостью auth-flow.

---

## 🧱 Production Hardening
Для production-использования дополнительно потребуются:
- защищённое хранение private key;
- ротация RSA ключей;
- rate limiting;
- audit logging security-событий;
- brute-force protection;
- мониторинг Redis;
- защита Redis от внешнего доступа;
- alerting при refresh token reuse detection;
- ограничение количества активных сессий;
- device/session metadata;
- admin revoke sessions;
- политика управления security incident;
- CORS / CSRF policy под конкретный тип клиента.

---

## ✅ Итоговая модель
Security model проекта строится слоями:
```text
RS256
  ↓
JWT signature validation

exp
  ↓
Token lifetime limit

Blacklist
  ↓
Token revoke before expiration

Refresh Whitelist
  ↓
Active Refresh token validation

Redis session state
  ↓
Session authority

Atomic rotation
  ↓
Race condition protection

Reuse detection
  ↓
Compromised session revoke
```

---

## 🐶 Bruno Security Flows
Проект включает __Bruno Collection__ для ручной демонстрации security-сценариев.

Bruno позволяет воспроизвести поведение системы через реальные HTTP-запросы:
- Refresh Token Rotation;
- Refresh Token Reuse Detection;
- Session Revocation;
- Logout All Sessions;
- отказ в доступе после отзыва сессии.

⚠️ Важно: __Bruno__ не является заменой автоматическим тестам безопасности.

__Bruno__ демонстрирует внешний API-flow, а __Pytest__ проверяет внутренние гарантии системы:
- состояние Redis session;
- refresh whitelist;
- token blacklist;
- отзыв access / refresh tokens;
- обработку reuse detection;
- корректность logout / logout-all.

---

## 🔗 Связанные документы
- [README](../README.md) ── Краткое описание проекта.
- [ARCHITECTURE](./ARCHITECTURE.md) ── Архитектура проекта.
- [JWT_FLOW](./JWT_FLOW.md) ── Жизненный цикл токенов.
- [DEVELOPMENT](./DEVELOPMENT.md) ── Локальный запуск и команды разработки.
- [API_EXAMPLES](./API_EXAMPLES.md) ── Примеры API-запросов.
- [BRUNO](./BRUNO.md) ── Коллекция Bruno для воспроизведения Auth, Content и Security сценариев.