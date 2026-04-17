from django.urls import path
from apps.content.api.views import ContentHealthView

urlpatterns = [
    path("health/", ContentHealthView.as_view(), name="content-health"),
]