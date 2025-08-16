from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_COOK_TIME, MIN_INGREDIENT_QTY, NAME_FIELD_LIMIT

User = get_user_model()


class Ingredient(models.Model):
    """Справочник ингредиентов."""
    name = models.CharField(
        'Название',
        unique=True,
        max_length=NAME_FIELD_LIMIT,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=NAME_FIELD_LIMIT,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """Теги для рецептов."""
    name = models.CharField(
        'Название',
        unique=True,
        max_length=NAME_FIELD_LIMIT,
    )
    slug = models.SlugField(
        'Slug',
        unique=True,
        max_length=NAME_FIELD_LIMIT,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Основная модель рецепта."""
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации (пользователь)',
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        'Название',
        max_length=NAME_FIELD_LIMIT,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField('Текстовое описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Используемые ингредиенты',
        related_name='recipes',
        through='IngredientInRecipe',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(
                MIN_COOK_TIME,
                message=f'Время должно быть не меньше {MIN_COOK_TIME} мин.',
            ),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name


class IngredientInRecipe(models.Model):
    """Связь ингредиента и рецепта с количеством."""
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredients_list',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='ingredients_list',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_QTY,
                message=f'Кол-во должно быть не меньше {MIN_INGREDIENT_QTY}.',
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self) -> str:
        return (
            f'{self.ingredient.name} ({self.ingredient.measurement_unit}) — '
            f'{self.amount}'
        )


class Favorite(models.Model):
    """Список избранных рецептов пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='favorites',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепты',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_favorite',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил "{self.recipes}" в избранное'


class ShoppingCart(models.Model):
    """Корзина покупок пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Владелец',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепты',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_shopping_cart',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил "{self.recipes}" в корзину'
