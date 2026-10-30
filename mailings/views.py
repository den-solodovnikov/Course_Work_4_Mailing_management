import threading

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView, ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from .models import Mailing, RecipientMail, Message
from .tasks import send_single_mailing_task


class IndexView(TemplateView):
    template_name = 'mailings/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Общее количество всех созданных рассылок
        context['total_mailings'] = Mailing.objects.count()

        # Количество активных рассылок
        context['active_mailings'] = Mailing.objects.filter(
            status='Запущена',
            start_time__lte=now,
            end_time__gte=now
        ).count()

        # Количество уникальных получателей
        context['unique_clients'] = RecipientMail.objects.count()

        return context


class RecipientMailDetailView(LoginRequiredMixin, DetailView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    context_object_name = "recipient"
    login_url = reverse_lazy("mailings:recipients")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.save()
        return self.object


class RecipientMailListView(LoginRequiredMixin, ListView):
    model = RecipientMail
    template_name = "mailings/recipients.html"
    context_object_name = "recipients"
    login_url = reverse_lazy("mailings:index")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class RecipientMailCreateView(LoginRequiredMixin, CreateView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    fields = ("email", "full_name", "comment")
    success_url = reverse_lazy('mailings:recipients')
    login_url = reverse_lazy("mailings:recipients")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class RecipientMailUpdateView(LoginRequiredMixin, UpdateView):
    model = RecipientMail
    template_name = "mailings/recipient_form.html"
    fields = ("email", "full_name", "comment")
    success_url = reverse_lazy('mailings:recipients')
    login_url = reverse_lazy("mailings:recipients")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = RecipientMail
    template_name = "mailings/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailings:recipients")
    login_url = reverse_lazy("mailings:index")


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "mailings/message_form.html"
    context_object_name = "message"
    login_url = reverse_lazy("mailings:messages")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.save()
        return self.object


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailings/messages.html"
    context_object_name = "messages"
    login_url = reverse_lazy("mailings:index")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = "mailings/message_form.html"
    fields = ("title", "content")
    success_url = reverse_lazy('mailings:messages')
    login_url = reverse_lazy("mailings:messages")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    template_name = "mailings/message_form.html"
    fields = ("title", "content")
    success_url = reverse_lazy('mailings:messages')
    login_url = reverse_lazy("mailings:messages")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:message_detail", kwargs={'pk': self.object.pk})


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("mailings:messages")
    login_url = reverse_lazy("mailings:index")


@method_decorator(cache_page(60 * 30), name='dispatch')


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailings/mailing_form.html"
    context_object_name = "mailing"
    login_url = reverse_lazy("mailings:mailings")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.save()
        return self.object


@method_decorator(cache_page(60 * 30), name='dispatch')
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailings/mailings.html"
    context_object_name = "mailings"
    login_url = reverse_lazy("mailings:index")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    template_name = "mailings/mailing_form.html"
    fields = ("start_time", "end_time", "status", "message", "recipients")
    success_url = reverse_lazy('mailings:mailings')
    login_url = reverse_lazy("mailings:mailings")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:recipient_detail", kwargs={'pk': self.object.pk})


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    template_name = "mailings/mailing_form.html"
    fields = ("start_time", "end_time", "status", "message", "recipients")
    success_url = reverse_lazy('mailings:mailings')
    login_url = reverse_lazy("mailings:mailings")

    # def get_success_url(self):
    #     return reverse_lazy("mailings:message_detail", kwargs={'pk': self.object.pk})


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailings")
    login_url = reverse_lazy("mailings:index")


@require_POST  # Запрещает GET-запросы в целях безопасности
def run_mailing_view(request, pk):
    # Находим рассылку или отдаем 404 ошибку
    mailing = get_object_or_404(Mailing, pk=pk)

    # Передаем ID рассылки в фоновую задачу Celery
    # Метод .delay() срабатывает мгновенно, не дожидаясь отправки писем
    send_single_mailing_task.delay(mailing.id)

    messages.success(request, f"Рассылка '{mailing.message.title}' "
                              f"успешно поставлена в очередь на отправку.")

    # Редирект обратно на страницу со списком рассылок или на детальную страницу
    return redirect("mailings:mailings")
