# DjangoJWT —  JWT FLOW

---

## Login Flow
```
1. Пользователь отправляет credentials.
2. Django аутентифицирует пользователя.
3. Создаётся session_id.
4. Генерируется Access token.
5. Генерируется Refresh token.
6. Refresh token сохраняется в Whitelist.
7. В Redis создаётся session.
8. Токены возвращаются клиенту.
```

---

# Access Token Validation Flow
```
1. Получен access token.
2. Проверяется RS256 signature.
3. Проверяется exp.
4. Проверяется token type.
5. Проверяется Blacklist.
6. Из Redis загружается session.
7. access_jti сравнивается с session.access_jti.
8. Пользователь аутентифицирован.
```

---

# Refresh Rotation Flow
```
1.  Получен Refresh token.
2.  Проверяется RS256 signature.
3.  Проверяется exp.
4.  Проверяется token type.
5.  Проверяется Blacklist.
6.  Проверяется Whitelist.
7.  Загружается session.
8.  Сравнивается refresh_jti.
9.  Старый Refresh удаляется из Whitelist.
10. Старый Refresh добавляется в Blacklist.
11. Старый Access добавляется в Blacklist.
12. Генерируется новый Access.
13. Генерируется новый Refresh.
14. Новый Refresh добавляется в Whitelist.
15. Session обновляется.
16. Новые токены возвращаются.
```

---

# Logout Flow
```
1.  Получен Refresh token.
2.  Проверяется RS256 signature.
3.  Проверяется exp.
4.  Проверяется token type.
5.  Проверяется Blacklist.
6.  Проверяется Whitelist.
7.  Загружается session.
8.  Сравнивается refresh_jti.
9.  Access token добавляется в Blacklist.
10. Refresh token добавляется в Blacklist.
11. Refresh удаляется из Whitelist.
12. Session удаляется.
13. Пользователь выходит из текущей сессии.
```

---

# Logout All Sessions Flow
```
1. Пользователь аутентифицирован.
2. Загружаются все session_id пользователя.
3. Загружается каждая session.
4. Все Access token Blacklist.
5. Все Refresh token Blacklist.
6. Все Refresh удаляются из Whitelist.
7. Все sessions удаляются.
8. Пользователь выходит из всех активных сессий.
```