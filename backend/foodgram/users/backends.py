from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()

class EmailBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None
        qs = User.objects.filter(email__iexact=email).order_by('id')
        user = qs.first()
        if not user:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None