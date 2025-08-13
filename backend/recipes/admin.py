from django.contrib import admin
from django.db.models import QuerySet

from .constants import ITEMS_ON_PAGE, MIN_INGREDIENT_QTY
from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)


class IngredientInline(admin.TabularInline):
    """Встроенное отображение ингредиентов в рецепте."""
    min_num: int = MIN_INGREDIENT_QTY
    model = IngredientInRecipe


class CommonRecipesAdmin(admin.ModelAdmin):
    """Базовый класс админки для моделей приложения `recipes`."""
    list_per_page: int = ITEMS_ON_PAGE


class IngredientAdmin(CommonRecipesAdmin):
    """Админка для модели ингредиента."""
    list_display: tuple[str, str] = (
        'name',
        'measurement_unit',
    )
    search_fields: tuple[str] = ('name',)
    list_display_links: tuple[str] = ('name',)
    inlines: tuple[type[admin.TabularInline]] = (IngredientInline,)


class FavoriteAdmin(CommonRecipesAdmin):
    """Админка для модели избранного."""
    list_display: tuple[str, str] = (
        'user',
        'recipes',
    )


class ShoppingCartAdmin(CommonRecipesAdmin):
    """Админка для модели корзины покупок."""
    list_display: tuple[str, str] = (
        'user',
        'recipes',
    )


class RecipeAdmin(CommonRecipesAdmin):
    """Админка для модели рецепта."""
    list_display: tuple[str, str, str, str] = (
        'name',
        'author',
        'pub_date',
        'count_in_favorite',
    )
    search_fields: tuple[str] = (
        'name',
        'author__username',
        'author__email',
        'tags__name',
        'tags__slug',
    )
    list_filter: tuple[str] = ('tags',)
    list_display_links: tuple[str] = ('name',)
    inlines: tuple[type[admin.TabularInline]] = (IngredientInline,)

    def count_in_favorite(self, obj: Recipe) -> int:
        """Подсчет, сколько раз рецепт добавлен в избранное."""
        return Favorite.objects.filter(recipes=obj).count()

    count_in_favorite.short_description = 'Сколько раз в избранном'


class TagAdmin(CommonRecipesAdmin):
    """Админка для модели тега."""
    list_display: tuple[str, str] = (
        'name',
        'slug',
    )
    list_display_links: tuple[str] = ('name',)


admin.site.empty_value_display = '—'
admin.site.site_header = 'Панель управления Foodgram'
admin.site.site_title = 'Foodgram'

admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)

