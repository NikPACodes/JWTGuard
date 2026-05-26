import pytest
from apps.auth_jwt.services.jwt_service import decode_token


@pytest.mark.django_db
def test_logout_revokes_current_session(api_client, user, token_store):
    """
    Тест logout текущей session.

    Проверки:
    - session удаляется из Redis;
    - refresh удаляется из whitelist;
    - refresh добавляется в blacklist;
    - access добавляется в blacklist;
    - access token больше не даёт доступ к protected endpoint.
    """
    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    access = login_response.data['access']
    refresh = login_response.data['refresh']
    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.post(
        "/api/auth/logout/",
        {
            "refresh": refresh
        },
        format="json",
    )

    assert response.status_code in (200, 204)
    assert token_store.get_session(session_id=refresh_payload['sid']) is None

    assert not token_store.is_refresh_whitelisted(jti=refresh_payload['jti'])
    assert token_store.is_blacklisted(jti=refresh_payload['jti'])
    assert token_store.is_blacklisted(jti=access_payload['jti'])

    profile_response = api_client.get('/api/auth/profile/')
    assert profile_response.status_code == 403


@pytest.mark.django_db
def test_logout_all_revokes_all_user_sessions(api_client, user):
    """
    Тест logout_all для всех пользовательских sessions.

    Сценарий:
    - пользователь логинится с двух устройств;
    - выполняется logout_all.

    Проверки:
    - все sessions удаляются;
    - все access токены становятся невалидными;
    - все refresh токены становятся невалидными;
    - protected endpoints возвращают 403.
    """
    login_1 = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    login_2 = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    access_1 = login_1.data['access']
    access_2 = login_2.data['access']
    refresh_1 = login_1.data['refresh']
    refresh_2 = login_2.data['refresh']

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_1}")

    response = api_client.post('/api/auth/logout-all/')
    assert response.status_code in (200, 204)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_1}")
    profile_1 = api_client.get('/api/auth/profile/')
    assert profile_1.status_code == 403

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_2}")
    profile_2 = api_client.get('/api/auth/profile/')
    assert profile_2.status_code == 403

    refresh_response_1 = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": refresh_1
        },
        format="json",
    )
    assert refresh_response_1.status_code == 403

    refresh_response_2 = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": refresh_2
        },
        format="json",
    )
    assert refresh_response_2.status_code == 403