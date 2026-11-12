from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_active", "is_subscribed", "is_manager")
    actions = ["block_users", "disable_subscriptions"]

    # Менеджер видит раздел и список пользователей
    def has_module_permission(self, request):
        return request.user.is_superuser or getattr(request.user, "is_manager", False)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    # Полный запрет на создание, редактирование и удаление кого-либо для менеджера
    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # Блокировка (доступно менеджеру без права на редактирование)
    @admin.action(description="Заблокировать выбранных пользователей")
    def block_users(self, request, queryset):
        # Исключаем самого менеджера и суперпользователей из списка на блокировку
        safe_qs = queryset.exclude(id=request.user.id).exclude(is_superuser=True)
        safe_qs.update(is_active=False)

    # Отключение рассылок
    @admin.action(description="Отключить рассылки выбранным пользователям")
    def disable_subscriptions(self, request, queryset):
        queryset.update(is_subscribed=False)