from django.db import models
from django.contrib.auth.models import AbstractUser
from  .managers import UserManager


class User(AbstractUser):
    """
    Кастомный пользователь на базе AbstractUser.

    Используем email как основной идентификатор.
    """
    username = models.CharField(max_length=150, unique=True, blank=False, null=False, db_index=True)
    email = models.EmailField(unique=True, blank=False, null=False, db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email