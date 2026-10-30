from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from mailings.models import Mailing, Message, RecipientMail, Mailing, MailingAttempt
from mailings.services import send_mailing_service
from mailings.tasks import send_single_mailing_task
from users.models import User


@admin.register(User)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ["is_superuser", "username", "first_name", "last_name", "email", "phone", "country", "avatar"]
    list_filter = ("email",)
    search_fields = ("email", "phone")

@admin.register(Mailing)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ["start_time", "end_time", "status", "message_title", "recipients_list"]
    list_filter = ("status",)
    search_fields = ("status",)
    actions = ["trigger_mailing"]

    def message_title(self, obj):
        return obj.message

    def recipients_list(self, obj):
        return ", ".join([str(recipients) for recipients in obj.recipients.all()])

    @admin.action(description='Отправить выбранные рассылки через Celery')
    def trigger_mailing(self, request, queryset):
        for mailing in queryset:
            # Отправляем в фоновую очередь
            send_single_mailing_task.delay(mailing.id)

        self.message_user(
            request,
            f"Выбранные рассылки ({queryset.count()} шт.) отправлены в очередь Celery на обработку.",
            level=messages.SUCCESS
        )

    # @admin.action(description='Запустить выбранные рассылки вручную')
    # def trigger_mailing(self, request, queryset):
    #     for mailing in queryset:
    #         try:
    #             result = send_mailing(mailing.id)
    #             self.message_user(request, f"Рассылка {mailing.id}: {result}", messages.SUCCESS)
    #         except ValidationError as e:
    #             self.message_user(request, f"Рассылка {mailing.id}: {e.message}", messages.ERROR)
    #         except Exception as e:
    #             self.message_user(request, f"Рассылка {mailing.id}: Критическая ошибка {e}", messages.ERROR)


@admin.register(Message)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ["title", "content"]
    list_filter = ("title",)
    search_fields = ("title", "content")


@admin.register(RecipientMail)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "comment"]
    list_filter = ("full_name",)
    search_fields = ("full_name", "email")


@admin.register(MailingAttempt)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ["attempt_time", "status", "server_response", "mailing"]
    list_filter = ("status",)
    search_fields = ("status", "mailing")

    def mailing(self, obj):
        return obj.title

