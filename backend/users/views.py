from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from .models import Subscribe
from .permissions import CurrentUserOrAdmin
from .serializers import AvatarSerializer, SubscribeSerializer

User = get_user_model()


class MyUserViewSet(UserViewSet):
    """Расширенные эндпоинты для управления пользователями."""
    pagination_class = None  # Отключаем пагинацию по умолчанию

    def get_permissions(self):
        """Кастомная логика прав доступа."""
        return (CurrentUserOrAdmin(),) if self.action == 'me' else super().get_permissions()

    @action(
        methods=['put'],
        detail=False,
        url_path='me/avatar',
        permission_classes=(CurrentUserOrAdmin,),
        serializer_class=AvatarSerializer
    )
    def avatar(self, request):
        """Обновить аватар текущего пользователя."""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удалить аватар текущего пользователя."""
        request.user.avatar.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=(CurrentUserOrAdmin,)
    )
    def subscribe(self, request, id=None):
        """Подписаться или отписаться от пользователя."""
        target_user = get_object_or_404(User, id=id)
        if request.method == 'POST':
            return self._create_subscription(request.user, target_user)
        return self._remove_subscription(request.user, target_user)

    def _create_subscription(self, user, author):
        """Создать подписку."""
        if user == author:
            return Response({'error': 'Нельзя подписаться на себя'}, status=HTTP_400_BAD_REQUEST)
        if Subscribe.objects.filter(user=user, subscriptions=author).exists():
            return Response({'error': 'Подписка уже существует'}, status=HTTP_400_BAD_REQUEST)

        Subscribe.objects.create(user=user, subscriptions=author)
        return Response(
            SubscribeSerializer(author, context={'request': self.request}).data,
            status=HTTP_201_CREATED
        )

    def _remove_subscription(self, user, author):
        """Удалить подписку."""
        qs = Subscribe.objects.filter(user=user, subscriptions=author)
        if not qs.exists():
            return Response({'error': 'Подписка не найдена'}, status=HTTP_400_BAD_REQUEST)
        qs.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(CurrentUserOrAdmin,),
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Получить список всех подписок текущего пользователя."""
        authors_qs = User.objects.filter(subscriptions__user=request.user)
        page = self.paginate_queryset(authors_qs)
        serializer = SubscribeSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
