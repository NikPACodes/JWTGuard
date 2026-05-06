from django.urls import path, include
from apps.content.api.views import ContentHealthView, ContentItemView
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('', ContentItemView, basename='content')

urlpatterns = [
    path('health/', ContentHealthView.as_view(), name="content-health"),
    path('', include(router.urls)),
]