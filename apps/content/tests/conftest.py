import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def role_1_user(role_1):
    User = get_user_model()
    user = User.objects.create_user(
        email='role1@example.com',
        username='role1',
        password='StrongPass123!',
    )
    user.groups.add(role_1)
    return user


@pytest.fixture
def role_2_user(role_2):
    User = get_user_model()
    user = User.objects.create_user(
        email='role2@example.com',
        username='role2',
        password='StrongPass123!',
    )
    user.groups.add(role_2)
    return user