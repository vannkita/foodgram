from django.db.models import Sum
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import baseconv
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, 
    HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
)
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .filters import IngredientFilter, RecipeFilter
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .pagination import CustomPagination
from .permissions import CurrentUserOrAdmin, CurrentUserOrAdminOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeReadSerializer, RecipeRecordSerializer,
    RecipeSimpleSerializer, TagSerializer
)
from io import BytesIO


def create_shopping_list_file(shopping_cart):
    """Функция для создания тестового файла со списком продуктов."""
    file = BytesIO()
    for ingredient in shopping_cart:
        file.write(
            f"{ingredient['recipes__ingredients__name']}: "
            f"{ingredient['amount']} "
            f"{ingredient['recipes__ingredients__measurement_unit']}\n"
            .encode('utf-8')
        )
    file.seek(0)
    return file


class IngredientViewSet(ModelViewSet):
    """API для управления ингредиентами."""
    queryset = Ingredient.objects.all()
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """API для управления рецептами с расширенной функциональностью."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        """Автоматическое назначение текущего пользователя автором рецепта."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Динамический выбор сериализатора в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeRecordSerializer

    def get_permissions(self):
        """Гибкое управление правами доступа для разных операций."""
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return (CurrentUserOrAdminOrReadOnly(),)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки для рецепта."""
        recipe = self.get_object()
        encoded_id = baseconv.base64.encode(recipe.id)
        short_link = request.build_absolute_uri(
            reverse('short_link', kwargs={'encoded_id': encoded_id}))
        return Response({"short-link": short_link}, status=HTTP_200_OK)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзине покупок."""
        handler = self.add_recipe_to if request.method == 'POST' else self.delete_recipe_from
        return handler(ShoppingCart, request.user, pk)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        handler = self.add_recipe_to if request.method == 'POST' else self.delete_recipe_from
        return handler(Favorite, request.user, pk)

    def add_recipe_to(self, model, user, pk):
        """Вспомогательный метод для добавления рецепта в модель."""
        if model.objects.filter(user=user, recipes_id=pk).exists():
            return Response(
                {'errors': f'Рецепт {pk} уже добавлен в {model.__name__}.'},
                status=HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        model.objects.create(user=user, recipes=recipe)
        return Response(
            RecipeSimpleSerializer(recipe).data, 
            status=HTTP_201_CREATED
        )

    def delete_recipe_from(self, model, user, pk):
        """Вспомогательный метод для удаления рецепта из модели."""
        obj = model.objects.filter(user=user, recipes_id=pk)
        if not obj.exists():
            return Response(
                {'errors': f'Рецепт {pk} не найден в {model.__name__}.'},
                status=HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[CurrentUserOrAdmin]
    )
    def download_shopping_cart(self, request):
        """Генерация файла со списком покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).values(
            'recipes__ingredients__name',
            'recipes__ingredients__measurement_unit'
        ).annotate(
            amount=Sum('recipes__ingredients_list__amount')
        ).order_by('recipes__ingredients__name')

        file = create_shopping_list_file(shopping_cart)
        return FileResponse(
            file,
            content_type='text/plain',
            as_attachment=True,
            filename=f'{user}_shopping_list.txt'
        )


class TagViewSet(ModelViewSet):
    """API для работы с тегами рецептов."""
    queryset = Tag.objects.all()
    http_method_names = ['get']
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class ShortLinkView(APIView):
    """Обработчик коротких ссылок для рецептов."""
    permission_classes = (AllowAny,)

    def get(self, request, encoded_id):
        """Перенаправление с короткой ссылки на полный рецепт."""
        decoded_id = baseconv.base64.decode(encoded_id)
        recipe = get_object_or_404(Recipe, id=decoded_id)
        return HttpResponseRedirect(f'/recipes/{recipe.id}/')
