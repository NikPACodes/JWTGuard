# DjangoJWT — SECURITY MODEL

## Общая идея

Проект реализует управляемую JWT-аутентификацию с использованием Redis-backed session state.

__Security model__ основана на:
- RS256 асимметричном JWT;
- короткоживущем Access token;
- ротации Refresh token;
- Redis session authority;
- Token Revoke;
- валидации Refresh Whitelist.

---

# Threat Model

Система проектируется для снижения рисков:
- компрометации Access token;
- компрометации Refresh token;
- Replay attacks;
- сохранения активности session после logout.

---

# Безопасность Access Token

## Короткий TTL

Access token намеренно сделан короткоживущим для снижения ущерба от украденного Access token.


## Blacklist Revoke

Access token может быть принудительно инвалидирован до expiration через Blacklist.

Это используется для:
- _logout_;
- _logout all sessions_;
- _revoke session_;
- _refresh rotation_.


## Session Validation

Access token должен соответствовать активной Redis session.

Необходимое условие: 
```
payload.jti == session.access_jti
```

Это позволяет:
- revoke активных session;
- invalidate Access token до expiration;
- предотвращать использование неактуальных access token.

---

# Безопасность Refresh Token

Refresh token считается high-value credential.

Свойства:
- долгоживущий;
- хранится в Whitelist;
- ротируется при refresh;
- revoke при logout.


## Refresh Whitelist Validation

Refresh token считается активным только если:
- signature валиден;
- expiration валиден;
- token отсутствует в Blacklist;
- token присутствует в Whitelist;
- token соответствует активной session.


## Refresh Rotation

Во время refresh rotation:
- старый Refresh token добавляется в Blacklist;
- старый Refresh token удаляется из Whitelist;
- генерируется новый Refresh token;
- session обновляется новым refresh_jti.

Refresh rotation снижает риск replay attack и reuse старых Refresh token.


## Refresh Reuse Detection

Система использует Refresh Token Reuse Detection для выявления повторного использования 
уже отозванных Refresh token и компрометации session.

---

# Replay Attack Protection

Replay Attack Protection основана на:
- Refresh rotation;
- Refresh Blacklist validation;
- Refresh Whitelist validation;
- Redis session validation;
- Refresh reuse detection.

---

# Logout / Revoke 

При logout:
- Access token добавляется в Blacklist;
- Refresh token добавляется в Blacklist;
- Refresh token удаляется из Whitelist;
- session удаляется из Redis.

Это предотвращает использование session после logout.

---

# Session Authority

Redis выступает источником актуального session state.

JWT сам по себе НЕ считается достаточным для авторизации.

Авторизация требует:
```
valid JWT + active Redis session
```

---

# Security Limitations

## HTTPS Required

JWT-аутентификация должна использоваться только через HTTPS.

Передача JWT через HTTP создаёт риск компрометации токенов.


## Client-side Token Theft

Backend не может полностью защитить токены от кражи на стороне клиента.

Например:
- XSS-атак;
- вредоносного ПО;
- небезопасных расширений браузера;
- утечек client-side storage.

Поэтому Access token должен быть короткоживущим.

---

## Redis Compromise

Redis является критически важной частью системы безопасности.

Компрометация Redis может привести к:
- компрометации session;
- перехвату session;
- обходу revoke;
- несанкционированному управлению session.

Redis должен быть:
- изолирован;
- защищён паролем;
- недоступен из публичной сети.