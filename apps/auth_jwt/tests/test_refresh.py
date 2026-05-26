import pytest

from apps.auth_jwt.services.jwt_service import decode_token


@pytest.mark.django_db
def test_refresh_rotates_tokens_and_updates_session(api_client, user, token_store):
    """
    Тест успешной refresh rotation.

    Проверки:
    - endpoint возвращает новую пару access/refresh;
    - old refresh удаляется из whitelist;
    - old refresh добавляется в blacklist;
    - old access добавляется в blacklist;
    - new refresh добавляется в whitelist;
    - Redis session обновляется новыми JTI.
    """
    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    old_access = login_response.data['access']
    old_refresh = login_response.data['refresh']
    old_access_payload = decode_token(old_access)
    old_refresh_payload = decode_token(old_refresh)

    response = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": old_refresh
        },
        format="json",
    )

    assert response.status_code == 200

    new_access = response.data['access']
    new_refresh = response.data['refresh']
    new_access_payload = decode_token(new_access)
    new_refresh_payload = decode_token(new_refresh)

    assert new_access_payload['jti'] != old_access_payload['jti']
    assert new_refresh_payload['jti'] != old_refresh_payload['jti']

    assert new_access_payload['sid'] == old_access_payload['sid']
    assert new_refresh_payload['sid'] == old_refresh_payload['sid']

    assert not token_store.is_refresh_whitelisted(jti=old_refresh_payload['jti'])
    assert token_store.is_blacklisted(jti=old_refresh_payload['jti'])
    assert token_store.is_blacklisted(jti=old_access_payload['jti'])

    assert token_store.is_refresh_whitelisted(jti=new_refresh_payload['jti'])

    session = token_store.get_session(session_id=new_refresh_payload['sid'])
    assert session is not None
    assert session['access_jti'] == new_access_payload['jti']
    assert session['refresh_jti'] == new_refresh_payload['jti']


@pytest.mark.django_db
def test_old_access_token_does_not_work_after_refresh(api_client, user):
    """
    Тест invalidation old access token после refresh rotation.

    Проверки:
    - old access token после refresh больше невалиден;
    - protected endpoint возвращает 403.
    """
    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    old_access = login_response.data['access']
    old_refresh = login_response.data['refresh']

    refresh_response = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": old_refresh
        },
        format="json",
    )
    assert refresh_response.status_code == 200

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_access}")

    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 403