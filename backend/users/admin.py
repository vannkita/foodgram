from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .constants import ADMIN_PAGE_SIZE
from .models import MyUser, Subscribe


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Админка для модели подписок."""
    list_display = ('user', 'subscriptions')
    list_display_links = ('user',)
    list_per_page = ADMIN_PAGE_SIZE


# Добавляем поле avatar в стандартный UserAdmin
UserAdmin.fieldsets += (
    ('Дополнительные поля', {'fields': ('avatar',)}),
)

admin.site.register(MyUser, UserAdmin)
