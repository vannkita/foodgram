from rest_framework.permissions import (SAFE_METHODS,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly
                                        )


class CurrentUserOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешает полный доступ:
    - Автору объекта
    - Администратору
    Остальным - только чтение"""
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_staff
            or obj.author == request.user
        )


class CurrentUserOrAdmin(IsAuthenticated):
    """Строгий доступ только для автора или администратора."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.author == request.user
