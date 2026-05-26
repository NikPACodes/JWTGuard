import pytest


@pytest.mark.django_db
def test_profile_authentication_error(api_client):
    """
    Тест доступа к protected endpoint без Authorization header.

    Проверки:
    - endpoint возвращает 403;
    - доступ без access token запрещён.
    """
    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_profile_authentication_with_valid_access_token(api_client, user):
    """
    Тест доступа к protected endpoint с валидным access token.

    Проверки:
    - access token успешно проходит authentication;
    - endpoint возвращает 200;
    - пользователь определяется корректно.
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
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 200
    assert response.data['email'] == "user@example.com"


@pytest.mark.django_db
def test_profile_authentication_with_valid_refresh_token_error(api_client, user):
    """
    Тест использования refresh token вместо access token.

    Проверки:
    - refresh token не допускается для authentication;
    - endpoint возвращает 403.
    """
    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    refresh = login_response.data['refresh']
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")

    response = api_client.get('/api/auth/profile/')
    assert response.status_code == 403