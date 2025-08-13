from rest_framework.permissions import (SAFE_METHODS,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.request import Request
from rest_framework.views import View


class CurrentUserOrAdmin(IsAuthenticated):
    """Доступ к объекту только для его автора или администратора."""
    def has_object_permission(self, request: Request, view: View, obj):
        return (
            request.user.is_staff
            or getattr(obj, 'author', None) == request.user
        )


class CurrentUserOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Полный доступ — только у владельца объекта или администратора.
    Для остальных пользователей доступ разрешён только на чтение.
    """
    def has_object_permission(self, request: Request, view: View, obj):
        user = request.user
        if isinstance(obj, type(user)) and obj == user:
            return True
        return request.method in SAFE_METHODS or user.is_staff
