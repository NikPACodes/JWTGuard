from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    """
    Менеджер для кастомного пользователя.

    Зачем нужен:
    - гарантирует, что email обязателен и нормализуется (приводится к стандартному виду)
    - корректно хеширует пароль через set_password()
    - корректно создаёт суперпользователя (is_staff/is_superuser)
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)