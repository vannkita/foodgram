from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from .constants import (EMAIL_LEN_LIMIT, FIRST_NAME_LEN_LIMIT,
                        LAST_NAME_LEN_LIMIT, USERNAME_LEN_LIMIT)


class MyUser(AbstractUser):
    """Пользовательская модель с email в качестве логина."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        verbose_name='Никнейм',
        max_length=USERNAME_LEN_LIMIT,
        unique=True,
        help_text=(
            f'Максимум {USERNAME_LEN_LIMIT} символов. '
            'Разрешены буквы, цифры и @/./+/-/_'
        ),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=FIRST_NAME_LEN_LIMIT,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=LAST_NAME_LEN_LIMIT,
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        max_length=EMAIL_LEN_LIMIT,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/avatars/',
        default=None,
        blank=True,
        null=True,
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права пользователя',
        blank=True,
        help_text='Конкретные права для этого пользователя',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Subscribe(models.Model):
    """Подписка пользователя на другого пользователя."""

    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    subscriptions = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписки',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscriptions'],
                name='unique_user_subscriptions',
            ),
        ]

    def clean(self) -> None:
        if self.user == self.subscriptions:
            raise ValidationError('Нельзя подписаться на самого себя.')
