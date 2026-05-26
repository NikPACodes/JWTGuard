import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from apps.auth_jwt.services.redis_token_store import RedisTokenStore


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def token_store():
    return RedisTokenStore()


@pytest.fixture(autouse=True)
def clean_redis(token_store):
    """
    Отчистка Redis до и после теста
    """
    # До
    token_store.redis_client.flushdb()
    yield
    # После
    token_store.redis_client.flushdb()


@pytest.fixture
def role_1():
    return Group.objects.create(name="role_1")


@pytest.fixture
def role_2():
    return Group.objects.create(name="role_2")


@pytest.fixture
def user(role_1):
    User = get_user_model()
    user = User.objects.create_user(
        email="user@example.com",
        username="user",
        password="StrongPass123!",
    )
    user.groups.add(role_1)
    return user