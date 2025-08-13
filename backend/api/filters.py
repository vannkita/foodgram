from django_filters.rest_framework import FilterSet, BooleanFilter
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Кастомный фильтр для рецептов с расширенными возможностями."""
    author = CharFilter()
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = BooleanFilter(method='filter_favorite')
    is_in_shopping_cart = BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorite(self, queryset, name, value):
        """Фильтрация по наличию в избранном."""
        user = self.request.user
        return queryset.filter(favorites__user=user) if value and user.is_authenticated else queryset

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтрация по наличию в корзине покупок."""
        user = self.request.user
        return queryset.filter(shopping_cart__user=user) if value and user.is_authenticated else queryset


class IngredientFilter(FilterSet):
    """Быстрый поиск ингредиентов по началу названия."""
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
