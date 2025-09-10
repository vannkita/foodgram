from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)


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
        link = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return Response({"short-link": link}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Управляет добавлением/удалением рецепта в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'GET':
            is_favorited = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
            return Response(
                {'is_favorited': is_favorited},
                status=status.HTTP_200_OK,
            )
        elif request.method == 'POST':
            if Favorite.objects.filter(
                user=request.user,
                recipe=recipe,
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user,
                                               recipe=recipe)
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite_delete(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепт не в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Управляет добавлением/удалением рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'GET':
            is_in_cart = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
            return Response(
                {'is_in_shopping_cart': is_in_cart},
                status=status.HTTP_200_OK,
            )
        elif request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe,
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        elif request.method == 'DELETE':
            cart = ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe)
            if not cart.exists():
                return Response(
                    {'errors': 'Рецепт не в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
            shopping_list.append(f"{name}: {amount} {unit}")

        content = "Список покупок:\n\n" + "\n".join(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; '
            'filename="shopping_list.txt"'
        )
        return response
