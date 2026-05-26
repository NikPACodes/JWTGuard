import pytest

from apps.auth_jwt.services.jwt_service import decode_token


@pytest.mark.django_db
def test_login_success_creates_tokens_and_session(api_client, user, token_store):
    """
    Тест успешный login flow.

    Проверки:
    - endpoint возвращает 200;
    - создаются access и refresh токены;
    - access/refresh содержат корректные payload fields;
    - refresh добавляется в Redis whitelist;
    - Redis session создаётся;
    - session содержит корректные access_jti и refresh_jti;
    - user_sessions индекс содержит sid текущей session.
    """
    response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )
    assert response.status_code == 200

    access = response.data['access']
    refresh = response.data['refresh']
    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)
    assert access_payload['type'] == "access"
    assert access_payload['sid'] == refresh_payload['sid']
    assert access_payload['sub'] == str(user.id)
    assert refresh_payload['type'] == "refresh"
    assert refresh_payload['sub'] == str(user.id)

    assert token_store.is_refresh_whitelisted(jti=refresh_payload['jti'])

    session = token_store.get_session(session_id=refresh_payload['sid'])
    assert session is not None
    assert session['access_jti'] == access_payload['jti']
    assert session['refresh_jti'] == refresh_payload['jti']

    user_session_ids = token_store.get_user_session_ids(user_id=user.id)
    assert refresh_payload['sid'] in user_session_ids


@pytest.mark.django_db
def test_login_with_invalid_credentials_returns_error(api_client, user):
    """
    Тест login с неверными credentials.

    Проверка:
    - endpoint возвращает 403
    """
    response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "wrong-password",
        },
        format="json",
    )

    assert response.status_code == 403