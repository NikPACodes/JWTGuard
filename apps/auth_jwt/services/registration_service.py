from __future__ import annotations
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework.exceptions import ValidationError

User = get_user_model()


@transaction.atomic
def register_user(*, email: str, username: str, password: str, role: str):
    """
    Сервис регистрации нового пользователя
    """
    try:
        group = Group.objects.get(name=role)
    except Group.DoesNotExist as exc:
        raise ValidationError(
            {"role": "Выбранная роль не найдена.."}
        ) from exc

    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
    )
    user.groups.add(group)
    return user