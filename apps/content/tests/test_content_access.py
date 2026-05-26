import pytest
from apps.content.models import ContentItem


@pytest.mark.django_db
def test_role_1_sees_only_allowed_content(api_client, role_1, role_2, role_1_user):
    """
    Тест фильтрации по role_1.

    Проверки:
    - пользователь role_1 видит общий контент;
    - пользователь role_1 видит свой контент;
    - пользователь role_1 НЕ видит контент role_2.
    """
    common = ContentItem.objects.create(
        title='Общий',
        body='Общий контент',
    )
    common.allowed_groups.add(role_1, role_2)

    role_1_content = ContentItem.objects.create(
        title='Роль 1',
        body='Контент для роли 1',
    )
    role_1_content.allowed_groups.add(role_1)

    role_2_content = ContentItem.objects.create(
        title='Роль 2',
        body='Контент для роли 2',
    )
    role_2_content.allowed_groups.add(role_2)

    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "role1@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    access = login_response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api_client.get('/api/content/')
    assert response.status_code == 200

    titles = {item['title'] for item in response.data}
    assert "Общий" in titles
    assert "Роль 1" in titles
    assert "Роль 2" not in titles


@pytest.mark.django_db
def test_role_2_sees_only_allowed_content(api_client, role_1, role_2, role_2_user):
    """
    Тест фильтрации по role_2.

    Проверки:
    - пользователь role_2 видит общий контент;
    - пользователь role_2 видит свой контент;
    - пользователь role_2 НЕ видит контент role_1.
    """
    common = ContentItem.objects.create(
        title='Общий',
        body='Общий контент',
    )
    common.allowed_groups.add(role_1, role_2)

    role_1_content = ContentItem.objects.create(
        title='Роль 1',
        body='Контент для роли 1',
    )
    role_1_content.allowed_groups.add(role_1)

    role_2_content = ContentItem.objects.create(
        title='Роль 2',
        body='Контент для роли 2',
    )
    role_2_content.allowed_groups.add(role_2)

    login_response = api_client.post(
        "/api/auth/login/",
        {
            "email": "role2@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    access = login_response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api_client.get('/api/content/')
    assert response.status_code == 200

    titles = {item['title'] for item in response.data}
    assert "Общий" in titles
    assert "Роль 2" in titles
    assert "Роль 1" not in titles