# DjangoJWT — Архитектура

## Общая идея

Проект реализует управляемую JWT-аутентификацию с использованием стека:
- _Django_
- _Django REST Framework_
- _PyJWT_
- _Redis_
- _PostgreSQL_

Ключевая архитектурная идея:
```
JWT + Redis Session State
```

__JWT__ — используется как переносимый authentication credential.  
__Redis__ — выступает источником актуального состояния сессии.

---

# Архитектура аутентификации

## Типы токенов

Система использует два типа JWT-токенов:


### Access Token

__Короткоживущий__ токен для авторизации API-запросов.

Свойства:
- короткий TTL;
- подпись `RS256`;
- содержит `sid` и `jti`;
- _НЕ хранится_ в Whitelist;
- добавляется в Blacklist после Revoke.


### Refresh Token
__Долгоживущий__ токен для обновления токенов.

Свойства:
- длинный TTL;
- хранится в Redis Whitelist;
- ротируется при Refresh;
- добавляется в Blacklist после Revoke/Rotation.


---

# Почему PyJWT, а не SimpleJWT

В проекте намеренно было принято решение использовать `PyJWT` вместо `django-rest-framework-simplejwt`, 
по следующим причинам:
- возможность полного контроля над жизненным циклом токенов;
- собственная __Redis session model__;
- собственная __Blacklist__ / __Whitelist__ логика;
- собственная __refresh rotation__ реализация;
- возможность дальнейшего выделения в отдельный auth-service.


---

# Почему RS256

В проекте, принято решение, использовать `RS256 (RSA SHA-256)` вместо классического `HS256`.

Основные причины: 
- асимметричная криптография;
- _private key_ подписывает токены;
- _public key_ проверяет токены;
- _public key_ можно безопасно распространять между сервисами;
- проще переход к микросервисной архитектуре.


---
# Access Token

## Почему для Access Token НЕ используется Whitelist

Проект намеренно не использует __Whitelist__ для __Access token__.

Причины:

- Access token короткоживущий;
- __Whitelist__ создаёт дополнительную нагрузку на __Redis__;
- может быть добавлен в __Blacklist__ после _revoke_;
- каждый API-запрос потребовал бы дополнительного Redis lookup;
- главным долгоживущим credential системы является Refresh token.


Вместо этого __Access token__ проходит:
1. проверку `RS256` _signature_;
2. проверку _expiration_;
3. проверку _token type_;
4. проверку _Blacklist_;
5. проверку _Redis session_;
6. проверку соответствия `access_jti` активной _session state_.



---

# Refresh Token

__Refresh token__ является главным долгоживущим credential.

Refresh token:
- хранится в __Redis Whitelist__;
- связан с активной _session_;
- ротируется при _refresh_;
- _revoke_ при _logout_;
- попадает в __Blacklist__ после _rotation/revoke_.

---

# Redis Session Model

Redis выступает в качестве `Session Authority`.

JWT сам по себе НЕ является окончательным источником правды.

Каждый __Access token__ должен соответствовать активному __Redis session state__.


---

# Структура Redis Keys

### Refresh Whitelist
```
jwt:white:refresh:{jti}
```

### Blacklist
```
jwt:black:{jti}
```

### Session Storage
```
jwt:session:{sid}
```

### User Sessions Index
```
jwt:user_sessions:{user_id}
```

---

# Атомарность Refresh Rotation

Для атомарности __Refresh rotation__ в проекте используется __Redis transaction pipeline__.

Причины:
- предотвратить _race condition_;
- предотвратить _double refresh_;
- гарантировать единое актуальное состояние _Refresh token_.


---

# Refresh Reuse Detection

Реализована _Refresh Token Reuse Detection_ для выявления аномалий и компрометации _Refresh_ токенов, 
по следующему сценарию:
1. _Refresh token_ ротируется.
2. Старый _refresh_ становится _invalid_.
3. Старый _refresh_ используется повторно.
4. Система обнаруживает _reuse_.
5. _Session_ считается _compromised_.
6. _Session revoke_.


---

# Возможности дальнейшего развития

Текущая архитектура изначально проектируется с возможностью дальнейшего выделения в _Standalone Auth Service_.

Потенциальное развитие: _Standalone JWT Auth Service_.