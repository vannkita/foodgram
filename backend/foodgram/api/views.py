from http import HTTPStatus
from django.contrib.auth import authenticate, get_user_model
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)
from foodgram.constants import DEFAULT_PAGE_SIZE
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow

User = get_user_model()


# Вью для рецептов
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор для действия."""
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохраняет новый рецепт."""
        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': link}, status=HTTPStatus.OK)

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Управляет добавлением/удалением рецепта в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'GET':
            is_favorited = recipe.favorited_by.filter(
                user=request.user).exists()
            return Response(
                {'is_favorited': is_favorited},
                status=HTTPStatus.OK,
            )
        elif request.method == 'POST':
            if recipe.favorited_by.filter(user=request.user).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=HTTPStatus.CREATED,
            )
        elif request.method == 'DELETE':
            favorite = recipe.favorited_by.filter(user=request.user)
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не в избранном.'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite_delete(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = recipe.favorited_by.filter(user=request.user)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепт не в избранном.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Управляет добавлением/удалением рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'GET':
            is_in_cart = recipe.in_shopping_cart.filter(
                user=request.user).exists()
            return Response(
                {'is_in_shopping_cart': is_in_cart},
                status=HTTPStatus.OK,
            )
        elif request.method == 'POST':
            if recipe.in_shopping_cart.filter(user=request.user).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=HTTPStatus.CREATED,
            )
        elif request.method == 'DELETE':
            cart = recipe.in_shopping_cart.filter(user=request.user)
            if not cart.exists():
                return Response(
                    {'errors': 'Рецепт не в списке покупок.'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            cart.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Формирует и возвращает файл со списком покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(total_amount=Sum('amount'))
        shopping_list = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['total_amount']
            shopping_list.append(f'{name}: {amount} {unit}')
        content = 'Список покупок:\n\n' + '\n'.join(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; '
            'filename="shopping_list.txt"'
        )
        return response


# Вью для пользователей
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
        return Response(
            serializer.data, status=HTTPStatus.CREATED, headers=headers)

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
        return Response(serializer.data, status=HTTPStatus.OK)

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
        return Response(serializer.data, status=HTTPStatus.OK)

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
                {'errors': 'Нельзя подписаться на самого себя'},
                status=HTTPStatus.BAD_REQUEST
            )
        if user.following.filter(following=following).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя'},
                status=HTTPStatus.BAD_REQUEST
            )
        Follow.objects.create(user=user, following=following)
        serializer = CustomUserSerializer(
            following,
            context={'request': request}
        )
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, id=None):
        """Отписывает пользователя от другого пользователя."""
        user = request.user
        following = self.get_object()
        follow = user.following.filter(following=following)
        if not follow.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=HTTPStatus.BAD_REQUEST
            )
        follow.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        user = request.user
        following = User.objects.filter(following__user=user).order_by('id')
        page = request.query_params.get('page', 1)
        limit = int(request.query_params.get('limit', DEFAULT_PAGE_SIZE))
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
            status=HTTPStatus.OK
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
                {'non_field_errors': ['Неверный email или пароль.']}
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
            status=HTTPStatus.OK
        )
