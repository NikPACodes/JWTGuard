import pytest
import time
from django.conf import settings
from apps.auth_jwt.services.jwt_service import decode_token


@pytest.mark.django_db
def test_refresh_reuse_revokes_session(api_client, user, token_store):
    """
    Тест Refresh Token Reuse Detection.

    Сценарий:
    - выполняется login;
    - refresh успешно ротируется;
    - старый refresh используется повторно.

    Проверки:
    - reuse корректно детектится;
    - endpoint возвращает reuse error;
    - session отзывается;
    - новый refresh становится невалидным;
    - текущий access перестаёт работать.
    """
    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    old_refresh = login_response.data['refresh']

    first_refresh_response = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": old_refresh
        },
        format="json",
    )

    assert first_refresh_response.status_code == 200

    new_access = first_refresh_response.data['access']
    new_refresh = first_refresh_response.data['refresh']
    old_refresh_payload = decode_token(old_refresh)
    new_refresh_payload = decode_token(new_refresh)

    time.sleep(settings.JWT_REFRESH_REUSE_GRACE_SECONDS + 1)
    reuse_response = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": old_refresh
        },
        format="json",
    )

    assert reuse_response.status_code == 403
    assert reuse_response.data['detail'].code == "refresh_token_reuse_detected"

    session = token_store.get_session(session_id=old_refresh_payload['sid'])
    assert session is None
    assert not token_store.is_refresh_whitelisted(jti=new_refresh_payload['jti'])
    assert token_store.is_blacklisted(jti=new_refresh_payload['jti'])

    second_refresh_response = api_client.post(
        "/api/auth/refresh/",
        {
            "refresh": new_refresh
        },
        format="json",
    )
    assert second_refresh_response.status_code == 403

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
    profile_response = api_client.get('/api/auth/profile/')
    assert profile_response.status_code == 403