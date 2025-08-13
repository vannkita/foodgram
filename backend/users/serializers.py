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
    """Сериализатор для подписок."""
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

    def validate(self, data):
        subscriptions = self.instance
        user = self.context.get('request').user
        if Subscribe.objects.filter(
                subscriptions=subscriptions, user=user).exists():
            raise ValidationError(
                message='Вы уже подписаны на этого пользователя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == subscriptions:
            raise ValidationError(
                message='Вы не можете подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeForSubscriptionSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data
