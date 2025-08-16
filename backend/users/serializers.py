from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Recipe
from rest_framework import status
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from .models import Subscribe

User = get_user_model()


class MyUserSerializer(UserSerializer):
    """Сериализатор для пользователей."""
    is_subscribed = SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, subscriptions=obj).exists()

    class Meta:
        model = User
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'avatar',
        )


class AvatarSerializer(ModelSerializer):
    """Сериализатор для аватаров."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if not value:
            raise ValidationError(message='Передано пустое поле avatar.')
        return value


class RecipeForSubscriptionSerializer(ModelSerializer):
    """Сериализатор для рецептов пользователей-авторов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscribeSerializer(MyUserSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name',)

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""
        return obj.recipes.count()  # Предполагается, что у модели User есть related_name='recipes'

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя с учетом параметра recipes_limit."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()  # Предполагается, что у модели User есть related_name='recipes'
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        from recipes.serializers import RecipeSerializer  # Импортируйте ваш RecipeSerializer
        return RecipeSerializer(recipes, many=True, context={'request': request}).data