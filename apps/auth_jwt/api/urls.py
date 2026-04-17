from django.urls import path

from apps.auth_jwt.api.views import HealthView

#Временная заглушка для создания каркаса
urlpatterns = [
    path("health/", HealthView.as_view(), name="auth-health"),
]