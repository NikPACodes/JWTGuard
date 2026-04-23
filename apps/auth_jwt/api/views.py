from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework import permissions, status
from apps.auth_jwt.api.serializers import LoginSerializer, LogoutSerializer, RefreshSerializer
from apps.auth_jwt.services.auth_service import login_user, logout_all_sessions, logout_session, refresh_tokens



#Временная заглушка для создания каркаса
class HealthView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "auth"})


class ProfileView(APIView):
    """
    Профиль
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        groups = list(request.user.groups.values_list("name", flat=True))
        return Response(
            {
                "id": request.user.id,
                "email": request.user.email,
                "username": request.user.username,
                "groups": groups,
            },
            status=status.HTTP_200_OK,
        )


class LoginView(GenericAPIView):
    """
    Авторизация.
    AllowAny т.к. нет Access токена
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return Response(tokens, status=status.HTTP_200_OK)


class RefreshView(GenericAPIView):
    """
    Обновление токена с ротацией.
    AllowAny т.к. Access токен уже истек
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = refresh_tokens(refresh_token=serializer.validated_data["refresh"])
        return Response(tokens, status=status.HTTP_200_OK)


class LogoutView(GenericAPIView):
    """
    Обновление токена с ротацией.
    AllowAny т.к. делаем logout_session на основе Refresh токена (Access может отсутствовать)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        logout_session(refresh_token=serializer.validated_data["refresh"])
        return Response({"detail": "Logout."}, status=status.HTTP_200_OK)


class LogoutAllView(APIView):
    """
    Обновление токена с ротацией.
    IsAuthenticated т.к. logout_all_sessions делаем на основе User
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout_all_sessions(user=request.user)
        return Response({"detail": "Logout из всех сессий."}, status=status.HTTP_200_OK)