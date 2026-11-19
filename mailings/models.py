from django.conf import settings
from django.utils import timezone

from django.db import models


class Message(models.Model):
    title = models.CharField(
        max_length=150,
        verbose_name="Тема письма",
        help_text="Введите тему",
    )
    content = models.TextField(
        verbose_name="Содержимое",
        help_text="Введите текст",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"
        ordering = ("title",)


class RecipientMail(models.Model):
    email = models.EmailField(
        max_length=150,
        unique=True,
        verbose_name="Email",
        help_text="Введите адрес электронной почты",
        null=True,
        blank=True,
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="Ф.И.О.",
        help_text="Введите Ф.И.О.",
    )
    comment = models.TextField(
        verbose_name="Комментарий",
        help_text="Введите комментарий",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылок"

    def __str__(self):
        return self.email


class Mailing(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создана"
        STARTED = "started", "Запущена"
        COMPLETED = "completed", "Завершена"

    start_time = models.DateTimeField(
        verbose_name="Время начала рассылки",
        help_text="Введите дату и время запуска рассылки 'YYYY-MM-DD HH:MM:SS'",
        blank=True,
    )
    end_time = models.DateTimeField(
        verbose_name="Время окончания рассылки",
        help_text="Введите дату и время окончания запуска рассылки 'YYYY-MM-DD HH:MM:SS'",
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name="Статус отправки",
        help_text="Выберите состояние письма",
    )
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(RecipientMail)

    def update_status(self, save=True):
        """Динамически вычисляет и при необходимости сохраняет статус рассылки."""
        now = timezone.now()

        if now < self.start_time:
            new_status = self.Status.CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.Status.STARTED
        else:
            new_status = self.Status.COMPLETED

        if self.status != new_status:
            self.status = new_status
            if save:
                self.save(update_fields=["status"])

        return self.status

    def save(self, *args, **kwargs):
        # Автоматический пересчёт статуса перед каждым сохранением объекта
        if "update_fields" not in kwargs or "status" not in kwargs["update_fields"]:
            self.update_status(save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class MailingAttempt(models.Model):
    # Статусы попытки в виде кортежа для поля выбора (Choices)
    STATUS_CHOICES = [
        ("success", "Успешно"),
        ("failed", "Не успешно"),
    ]

    # Дата и время попытки
    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время попытки"
    )

    # Статус попытки
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус"
    )

    server_response = models.TextField(
        blank=True, null=True, verbose_name="Ответ почтового сервера"
    )

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-attempt_time"]  # Свежие попытки будут вверху

    def __str__(self):
        return f"Попытка для {self.mailing.id} ({self.status}) от {self.attempt_time.strftime('%d.%m.%Y %H:%M')}"
