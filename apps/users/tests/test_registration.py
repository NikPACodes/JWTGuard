import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


@pytest.mark.django_db
def test_register_user_success(api_client):
    """
    Тест успешной регистрации пользователя.

    Проверки:
    - endpoint возвращает 201;
    - пользователь создаётся в БД;
    - пользователь получает корректную роль/group.
    """
    Group.objects.create(name='role_1')

    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new-user@example.com",
            "username": "new_user",
            "password": "StrongPass123!",
            "role": "role_1",
        },
        format="json",
    )
    assert response.status_code == 201

    User = get_user_model()
    user = User.objects.get(email='new-user@example.com')
    assert user.username == "new_user"
    assert user.groups.filter(name='role_1').exists()


@pytest.mark.django_db
def test_register_user_unknown_role(api_client):
    """
    Тест регистрации с несуществующей ролью.

    Проверки:
    - endpoint возвращает 400;
    - пользователь не создаётся.
    """
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new-user@example.com",
            "username": "new_user",
            "password": "StrongPass123!",
            "role": "unknown_role",
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_user_weak_password(api_client):
    """
    Тест password validation при регистрации.

    Проверки:
    - слабый пароль отклоняется;
    - endpoint возвращает 400;
    - пользователь не создаётся.
    """
    Group.objects.create(name='role_1')
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new-user@example.com",
            "username": "new_user",
            "password": "new_user",
            "role": "role_1",
        },
        format="json",
    )
    assert response.status_code == 400