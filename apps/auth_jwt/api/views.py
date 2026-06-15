# Copyright 2026 Nikolay Petukhov (NikPACodes)
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema
from apps.auth_jwt.api.serializers import (LoginSerializer, LogoutSerializer, RefreshSerializer, RegisterSerializer,
                                           HealthResponseSerializer, ProfileResponseSerializer, DetailResponseSerializer)
from apps.auth_jwt.services.auth_service import login_user, logout_all_sessions, logout_session, refresh_tokens
from apps.auth_jwt.services.registration_service import register_user


class HealthView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["Auth"],
        auth=[],
        responses={200: HealthResponseSerializer},
    )

    def get(self, request):
        return Response({"status": "ok", "service": "auth"})


class ProfileView(APIView):
    """
    Профиль
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        responses={200: ProfileResponseSerializer},
    )

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


class RegisterView(GenericAPIView):
    """
    Кастомная регистрация
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_user(
            email=serializer.validated_data["email"],
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
            role=serializer.validated_data["role"],
        )

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "groups": user.groups.values_list("name", flat=True).first(),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(GenericAPIView):
    """
    Авторизация.
    AllowAny т.к. нет Access токена
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
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
    authentication_classes = []
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
    authentication_classes = []
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

    @extend_schema(
        tags=["Auth"],
        request=None,
        responses={200: DetailResponseSerializer},
    )

    def post(self, request):
        logout_all_sessions(user=request.user)
        return Response({"detail": "Logout из всех сессий."}, status=status.HTTP_200_OK)