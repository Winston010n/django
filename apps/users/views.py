from django.contrib.auth import login, logout
from rest_framework import serializers, status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .tokens import jwt_payload, token_payload, user_payload


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Пользователи'],
        summary='Регистрация пользователя',
        description='Создаёт учётную запись и возвращает Django Token, JWT access и refresh.',
        request=RegisterSerializer,
        responses={201: inline_serializer(
            'RegisterResponse',
            fields={
                'message': serializers.CharField(),
                'user': UserSerializer(),
                'tokens': inline_serializer(
                    'RegisterTokens',
                    fields={
                        'jwt': inline_serializer(
                            'RegisterJWT',
                            fields={
                                'auth_type': serializers.CharField(),
                                'access': serializers.CharField(),
                                'refresh': serializers.CharField(),
                                'user': UserSerializer(),
                            },
                        ),
                        'token': serializers.CharField(),
                    },
                ),
            },
        )},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Пользователь успешно зарегистрирован",
                "user": user_payload(user),
                'tokens':{
                    'jwt': jwt_payload(user),
                    'token': token_payload(user)['token'],
                }
            },
            status=status.HTTP_201_CREATED
        )


class TokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Пользователи'],
        summary='Получить Django Token',
        description='Обменять имя пользователя и пароль на постоянный Django Token.',
        request=LoginSerializer,
        responses={200: inline_serializer(
            'DjangoTokenResponse',
            fields={
                'auth': serializers.CharField(),
                'token': serializers.CharField(),
                'user': UserSerializer(),
            },
        )},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(token_payload(user), status=status.HTTP_200_OK)

class TokenLogOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @extend_schema(
        tags=['Пользователи'],
        summary='Отозвать Django Token',
        description='Требует заголовок Authorization: Token <ключ>. Удаляет текущий токен.',
        request=None,
        responses={200: inline_serializer(
            'TokenLogoutResponse',
            fields={'message': serializers.CharField()},
        )},
    )
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(
            {'message': 'Токен Успешно удален'},
            status=status.HTTP_200_OK
        )

class JWTTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Пользователи'],
        summary='Получить пару JWT',
        description='Обменять имя пользователя и пароль на access и refresh JWT.',
        request=LoginSerializer,
        responses={200: inline_serializer(
            'JWTLoginResponse',
            fields={
                'auth_type': serializers.CharField(),
                'access': serializers.CharField(),
                'refresh': serializers.CharField(),
                'user': UserSerializer(),
            },
        )},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(jwt_payload(user), status=status.HTTP_200_OK)

class JWTTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Пользователи'],
        summary='Обновить access JWT',
        description='Принимает refresh-токен и возвращает новый access JWT.',
        responses={200: OpenApiResponse(description='Новая пара access и refresh JWT.')},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class JWTTokenLogOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        tags=['Пользователи'],
        summary='Отозвать refresh JWT',
        description=(
            'Требует Bearer access-токен и refresh-токен текущего пользователя '
            'в теле запроса. Отозванный refresh больше нельзя использовать.'
        ),
        request=TokenBlacklistSerializer,
        responses={200: inline_serializer(
            'JWTLogoutResponse',
            fields={'message': serializers.CharField()},
        )},
    )
    def post(self, request):
        refresh = RefreshToken(request.data.get('refresh', ''))
        token_user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if str(token_user_id) != str(request.user.pk):
            raise PermissionDenied('Можно отозвать только собственный refresh-токен.')
        serializer = TokenBlacklistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {'message': 'JWT refresh-токен успешно отозван'},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Пользователи'],
        summary='Войти в сессию',
        description='Выполняет вход через Django session authentication.',
        request=LoginSerializer,
        responses={200: OpenApiResponse(description='Сообщение об успешном входе и профиль пользователя.')},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        return Response(
            {
                "message": f"Вы успешно вошли в систему, {user.username}",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

class LogOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Пользователи'],
        summary='Выйти из сессии',
        description='Завершает текущую Django-сессию.',
        request=None,
        responses={200: OpenApiResponse(description='Сессия завершена.')},
    )
    def post(self, request):
        logout(request)
        return Response(
            {
                "message": "Вы успешно вышли из аккаунта",
            },
            status=status.HTTP_200_OK
        )

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Пользователи'],
        summary='Получить профиль',
        description='Возвращает профиль текущего пользователя. Требуется аутентификация.',
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Пользователи'],
        summary='Полностью обновить профиль',
        description='Заменяет редактируемые данные текущего пользователя.',
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Пользователи'],
        summary='Частично обновить профиль',
        description='Обновляет переданные поля профиля текущего пользователя.',
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
