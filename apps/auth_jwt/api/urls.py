from django.urls import path
from .views import HealthView, ProfileView, LoginView, LogoutView, RefreshView, LogoutAllView, RegisterView

urlpatterns = [
    path('health/', HealthView.as_view(), name='auth-health'),
    path('profile/', ProfileView.as_view(), name='auth-profile'),
    path('register/', RegisterView.as_view(), name="auth-register"),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('logout-all/', LogoutAllView.as_view(), name='auth-logout-all'),
    ]