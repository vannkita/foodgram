from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Менеджер для работы с моделью пользователя."""
    def create_user(self, email, password=None, **extra_fields):
        """Создает и сохраняет пользователя с указанным email и паролем."""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает и сохраняет суперпользователя с указанным email и паролем."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Модель пользователя с дополнительными полями."""
    avatar = models.ImageField(
        upload_to='images/',
        default='images/avatar-icon.png',
        null=True,
        blank=True
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        default=None
    )
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    """Модель подписки пользователя на другого пользователя."""
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            )
        ]
