from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from .models import Mailing, RecipientMail, Message, MailingAttempt
from .tasks import send_single_mailing_task


def get_mailing_stats(user):
    """Чтение статистики рассылок из кеша с учетом роли."""
    is_manager = getattr(user, "is_manager", False) or user.is_superuser
    cache_key = "mailing_stats_all" if is_manager else f"mailing_stats_user_{user.id}"

    stats = cache.get(cache_key)
    if stats is None:
        if is_manager:
            mailings_qs = Mailing.objects.all()
            attempts_qs = MailingAttempt.objects.all()
            recipients_qs = RecipientMail.objects.all()
        else:
            mailings_qs = Mailing.objects.filter(owner=user)
            attempts_qs = MailingAttempt.objects.filter(mailing__owner=user)
            recipients_qs = RecipientMail.objects.filter(owner=user)

        # Собираем готовый словарь со статистикой
        attempt_counts = attempts_qs.aggregate(
            total_attempts=Count("id"),
            success_attempts=Count("id", filter=Q(status="success")),
            failed_attempts=Count("id", filter=Q(status="failed")),
        )

        stats = {
            "total_mailings": mailings_qs.count(),
            "active_mailings": mailings_qs.filter(status="success").count(),
            "total_attempts": attempt_counts["total_attempts"] or 0,
            "success_attempts": attempt_counts["success_attempts"] or 0,
            "failed_attempts": attempt_counts["failed_attempts"] or 0,
            "unique_clients": recipients_qs.count(),
        }
        cache.set(cache_key, stats, timeout=300)  # Кеш на 5 минут

    return stats


@login_required
@cache_control(private=True, max_age=120)  # Клиентское кеширование на 120 секунд
def mailing_stats_view(request):
    stats = get_mailing_stats(request.user)
    return render(request, "mailings/index.html", {"stats": stats})


class OwnerQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        queryset = super().get_queryset()
        # Менеджеры или суперпользователи видят всё, остальные — только своё
        if self.request.user.is_superuser or self.request.user.groups.filter(name='Manager').exists():
            return queryset
        return queryset.filter(owner=self.request.user)


class RecipientMailDetailView(OwnerQuerysetMixin, DetailView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    context_object_name = "recipient"
    login_url = reverse_lazy("mailings:recipients")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.save()
        return self.object


class RecipientMailListView(OwnerQuerysetMixin, ListView):
    model = RecipientMail
    template_name = "mailings/recipients.html"
    context_object_name = "recipients"
    login_url = reverse_lazy("mailings:mailing_stats")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class RecipientMailCreateView(OwnerQuerysetMixin, CreateView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    fields = ("email", "full_name", "comment")
    success_url = reverse_lazy('mailings:recipients')
    login_url = reverse_lazy("mailings:recipients")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class RecipientMailUpdateView(OwnerQuerysetMixin, UpdateView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    fields = ("email", "full_name", "comment")
    success_url = reverse_lazy('mailings:recipients')
    login_url = reverse_lazy("mailings:recipients")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class RecipientDeleteView(OwnerQuerysetMixin, DeleteView):
    model = RecipientMail
    template_name = "mailings/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailings:recipients")
    login_url = reverse_lazy("mailings:mailing_stats")


class MessageDetailView(OwnerQuerysetMixin, DetailView):
    model = Message
    template_name = "mailings/message_form.html"
    context_object_name = "message"
    login_url = reverse_lazy("mailings:messages")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.save()
        return self.object


class MessageListView(OwnerQuerysetMixin, ListView):
    model = Message
    template_name = "mailings/messages.html"
    context_object_name = "messages"
    login_url = reverse_lazy("mailings:mailing_stats")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class MessageCreateView(OwnerQuerysetMixin, CreateView):
    model = Message
    template_name = "mailings/message_form.html"
    fields = ("title", "content")
    success_url = reverse_lazy('mailings:messages')
    login_url = reverse_lazy("mailings:messages")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class MessageUpdateView(OwnerQuerysetMixin, UpdateView):
    model = Message
    template_name = "mailings/message_form.html"
    fields = ("title", "content")
    success_url = reverse_lazy('mailings:messages')
    login_url = reverse_lazy("mailings:messages")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:message_detail", kwargs={'pk': self.object.pk})


class MessageDeleteView(OwnerQuerysetMixin, DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("mailings:messages")
    login_url = reverse_lazy("mailings:mailing_stats")


def get_cached_user_data(user):
    """Кеш с разделением по ролям."""
    if user.is_manager or user.is_superuser:
        cache_key = "user_data_all"
        queryset = Mailing.objects.select_related("owner").all()
    else:
        cache_key = f"user_data_{user.id}"
        queryset = Mailing.objects.filter(owner=user)

    # Пытаемся забрать готовый список из кеша
    items = cache.get(cache_key)

    if items is None:
        # Оборачиваем в list(), чтобы кешировались сами данные, а не ленивый QuerySet
        items = list(queryset)
        cache.set(cache_key, items, timeout=300)  # Кешируем на 5 минут

    return items


@login_required
@cache_control(private=True, max_age=60)  # Клиентское кеширование в браузере на 60 секунд
def data_list(request):
    items = get_cached_user_data(request.user)
    return render(request, "mailings/mailings.html", {"items": items})


@receiver([post_save, post_delete], sender=Mailing)
def clear_user_data_cache(sender, instance, **kwargs):
    # Удаляем кеш конкретного владельца и общий кеш менеджеров
    cache.delete(f"user_data_{instance.owner_id}")
    cache.delete("user_data_all")


class MailingCreateView(OwnerQuerysetMixin, CreateView):
    model = Mailing
    template_name = "mailings/mailing_form.html"
    fields = ("start_time", "end_time", "message", "recipients")
    success_url = reverse_lazy('mailings:mailings')
    login_url = reverse_lazy("mailings:mailings")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class MailingUpdateView(OwnerQuerysetMixin, UpdateView):
    model = Mailing
    template_name = "mailings/mailing_form.html"
    fields = ("start_time", "end_time", "status", "message", "recipients")
    success_url = reverse_lazy('mailings:mailings')
    login_url = reverse_lazy("mailings:mailings")

class MailingListView(OwnerQuerysetMixin, ListView):
    model = Mailing
    template_name = "mailings/mailings.html"
    fields = ("start_time", "end_time", "status", "message", "recipients")
    success_url = reverse_lazy('mailings:mailings')
    login_url = reverse_lazy("mailings:mailings")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:message_detail", kwargs={'pk': self.object.pk})


class MailingDeleteView(OwnerQuerysetMixin, DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailings")
    login_url = reverse_lazy("mailings:mailing_stats")


@require_POST  # Запрещает GET-запросы в целях безопасности
def run_mailing_view(request, pk):
    now = timezone.now()
    mailing = get_object_or_404(Mailing, pk=pk)

    if request.user.is_superuser:
        mailing = get_object_or_404(Mailing, pk=pk)
    else:
        mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)

    if now < mailing.start_time:
        messages.error(
            request,
            f"Невозможно запустить рассылку «{mailing}»: время начала ещё не наступило."
        )
        return redirect('mailings:mailings')

    if now > mailing.end_time:
        messages.error(
            request,
            f"Невозможно запустить рассылку «{mailing}»: время её проведения уже истекло."
        )
        return redirect('mailings:mailings')

    mailing.status = Mailing.Status.STARTED
    mailing.save(update_fields=['status'])

    send_single_mailing_task.delay(mailing.pk)
    messages.success(request, f"Рассылка «{mailing}» успешно поставлена в очередь.")

    return redirect('mailings:mailings')

