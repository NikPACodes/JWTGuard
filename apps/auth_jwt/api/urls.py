from django.urls import path
from .views import HealthView, ProfileView, LoginView, LogoutView, RefreshView, LogoutAllView

urlpatterns = [
    path('health/', HealthView.as_view(), name='auth-health'),
    path('profile/', ProfileView.as_view(), name='auth-me'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('logout-all/', LogoutAllView.as_view(), name='auth-logout-all'),
    ]