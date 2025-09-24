from django.contrib.auth import get_user_model
from django.templatetags.static import static
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Follow

User = get_user_model()


# Сериализаторы пользователей
class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'username': {'required': False, 'allow_null': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'password': {'required': True},
        }

    def validate(self, data):
        """Проверяет корректность введенных данных."""
        return data

    def create(self, validated_data):
        """Создает нового пользователя с переданными данными."""
        user = User.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с данными пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )

    def get_avatar(self, obj):
        return (
            obj.avatar.url
            if obj.avatar
            else static("images/avatar-icon.png")
        )

    def to_representation(self, instance):
        """Преобразует данные пользователя в JSON-представление."""
        try:
            return super().to_representation(instance)
        except Exception as e:
            raise serializers.ValidationError(f"Ошибка сериализации: {str(e)}")

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, following=obj).exists()

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя с учетом лимита."""
        try:
            from recipes.serializers import ShortRecipeSerializer
            request = self.context.get('request')
            recipes_limit = request.query_params.get('recipes_limit')
            queryset = obj.recipes.all().order_by('-id')
            if recipes_limit:
                queryset = queryset[:int(recipes_limit)]
            return ShortRecipeSerializer(
                queryset, many=True, context=self.context
            ).data
        except Exception:
            return []

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов пользователя."""
        return obj.recipes.count()


# Сериализаторы рецептов
class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.Serializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_id(self, value):
        """Проверяет существование ингредиента по id."""
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id={value} не существует.'
            )
        return value

    def validate_amount(self, value):
        """Проверяет, что количество ингредиента больше 0."""
        if value < 1:
            raise serializers.ValidationError(
                'Количество должно быть больше 0.'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'author'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        """Проверяет корректность данных рецепта."""
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        return data

    def create(self, validated_data):
        """Создает новый рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return instance

    def to_representation(self, instance):
        """Преобразует рецепт в JSON-представление."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов рецепта."""
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [
            {
                'id': ingredient.ingredient.id,
                'name': ingredient.ingredient.name,
                'measurement_unit': ingredient.ingredient.measurement_unit,
                'amount': ingredient.amount
            }
            for ingredient in ingredients
        ]

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
