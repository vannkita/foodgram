from django.contrib.auth import get_user_model
from django.templatetags.static import static
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from .models import Follow

User = get_user_model()


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
            'avatar',  # Заменили avatar_url на avatar
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
