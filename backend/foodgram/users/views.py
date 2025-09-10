from django.contrib.auth import authenticate, get_user_model
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import Follow
from .serializers import CustomUserCreateSerializer, CustomUserSerializer


User = get_user_model()


class UsersViewSet(DjoserUserViewSet):
    """Представление для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        """Определяет права доступа для различных действий."""
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        """Создает нового пользователя."""
        serializer = CustomUserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = CustomUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def me_avatar(self, request):
        """Обновляет аватар текущего пользователя."""
        serializer = CustomUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписывает пользователя на другого пользователя."""
        user = request.user
        following = self.get_object()
        if user == following:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(
            user=user,
            following=following
        ).exists():
            return Response(
                {"errors": "Вы уже подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.create(user=user, following=following)
        serializer = CustomUserSerializer(
            following,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, id=None):
        """Отписывает пользователя от другого пользователя."""
        user = request.user
        following = self.get_object()
        follow = Follow.objects.filter(user=user, following=following)
        if not follow.exists():
            return Response(
                {"errors": "Вы не подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        user = request.user
        following = User.objects.filter(
            following__user=user
        ).order_by('id')
        page = request.query_params.get('page', 1)
        limit = int(request.query_params.get('limit', 6))
        paginator = Paginator(following, limit)
        page_obj = paginator.get_page(page)
        serializer = CustomUserSerializer(
            page_obj,
            many=True,
            context={'request': request}
        )
        return Response(
            {
                'count': paginator.count,
                'next': (
                    page_obj.next_page_number()
                    if page_obj.has_next()
                    else None
                ),
                'previous': (
                    page_obj.previous_page_number()
                    if page_obj.has_previous()
                    else None
                ),
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )


class LoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователей."""

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        """Проверяет корректность введенных данных для входа."""
        email = data.get('email')
        password = data.get('password')
        user = authenticate(
            request=self.context['request'],
            username=email,
            password=password
        )
        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["Неверный email или пароль."]}
            )
        data['user'] = user
        return data


@method_decorator(csrf_exempt, name='dispatch')
class CustomAuthToken(APIView):
    """Представление для получения токена аутентификации."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Обрабатывает запрос на получение токена."""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                'auth_token': token.key,
                'user_id': user.pk,
                'email': user.email
            },
            status=status.HTTP_200_OK
        )
