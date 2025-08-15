from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.serializers import MyUserSerializer


class TagSerializer(ModelSerializer):
    """Сериализатор для тегов рецептов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    """Базовый сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForRecipeReadSerializer(ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте с количеством."""
    amount = SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, obj):
        """Получение количества ингредиента через промежуточную модель."""
        return obj.ingredients_list.last().amount


class IngredientForRecipeRecordSerializer(ModelSerializer):
    """Сериализатор для записи ингредиентов при создании рецепта."""
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для детального отображения рецепта."""
    tags = TagSerializer(many=True, read_only=True)
    author = MyUserSerializer(read_only=True)
    ingredients = IngredientForRecipeReadSerializer(many=True, read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_image(self, obj):
        if obj.image:
            return (f'http://{settings.DOMAIN}{settings.MEDIA_URL}',
                    f'{obj.image.name}')

        return None

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в корзине текущего пользователя."""
        user = self.context['request'].user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipes=obj
        ).exists()

    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном текущего пользователя."""
        user = self.context['request'].user
        return user.is_authenticated and Favorite.objects.filter(
            user=user, recipes=obj
        ).exists()


class RecipeRecordSerializer(ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""
    ingredients = IngredientForRecipeRecordSerializer(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    author = MyUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'author', 'image',
            'name', 'id', 'text', 'cooking_time'
        )

    def validate(self, data):
        """Базовая валидация обязательных полей."""
        required_fields = ('ingredients',
                           'tags',
                           'name',
                           'text',
                           'cooking_time'
                           )
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f'Обязательное поле: {field}',
                    code=status.HTTP_400_BAD_REQUEST
                )
        return data

    def validate_image(self, value):
        """Проверка наличия изображения."""
        if not value:
            raise ValidationError(
                'Изображение обязательно для загрузки',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    def validate_tags(self, value):
        """Проверка корректности тегов."""
        if not value:
            raise ValidationError(
                'Необходим хотя бы один тег',
                code=status.HTTP_400_BAD_REQUEST
            )
        if len(value) != len(set(value)):
            raise ValidationError(
                'Теги должны быть уникальными',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    def validate_ingredients(self, value):
        """Проверка корректности ингредиентов."""
        if not value:
            raise ValidationError(
                'Необходим хотя бы один ингредиент',
                code=status.HTTP_400_BAD_REQUEST
            )
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise ValidationError(
                'Ингредиенты должны быть уникальными',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    @atomic
    def create_ingredients_in_recipe(self, ingredients, recipe):
        """Пакетное создание связей ингредиентов с рецептом."""
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    @atomic
    def create(self, validated_data):
        """Создание рецепта со связанными объектами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_in_recipe(ingredients, recipe)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        """Обновление рецепта с полной заменой связей."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_in_recipe(ingredients, instance)
        return instance

    def to_representation(self, instance):
        """Использование read-сериализатора для ответа."""
        return RecipeReadSerializer(
            instance,
            context={'request': self.context['request']}
        ).data


class RecipeSimpleSerializer(ModelSerializer):
    """Упрощенный сериализатор для рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
