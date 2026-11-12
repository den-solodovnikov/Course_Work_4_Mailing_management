from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from mailings.models import Mailing, Message, RecipientMail, Mailing, MailingAttempt
from mailings.services import send_mailing_service
from mailings.tasks import send_single_mailing_task
from users.models import User


@admin.register(Message)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ("title", "owner")

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Менеджер и админ видят все записи, обычный пользователь — только свои
        if request.user.is_superuser or getattr(request.user, "is_manager", False):
            return qs
        return qs.filter(owner=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj or request.user.is_superuser:
            return True
        # Редактировать можно только свои записи (даже менеджеру)
        return obj.owner == request.user

    def has_delete_permission(self, request, obj=None):
        if not obj or request.user.is_superuser:
            return True
        # Удалять можно только свои записи
        return obj.owner == request.user
