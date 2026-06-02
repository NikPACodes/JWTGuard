from django.apps import AppConfig


class AuthJwtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'apps.auth_jwt'
    verbose_name = 'AuthJWT'
    label = 'auth_jwt'

    def ready(self):
        import apps.auth_jwt.schema  # noqa: F401