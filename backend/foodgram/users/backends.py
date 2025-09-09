from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """Бэкенд аутентификации по email."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Аутентифицирует пользователя по email и паролю."""
        email = kwargs.get('email', username)
        try:
            user = User.objects.get(email__iexact=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        """Получает пользователя по его идентификатору."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None