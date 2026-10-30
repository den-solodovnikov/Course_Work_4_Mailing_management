from django.utils import timezone

from django.core.exceptions import ValidationError
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
        verbose_name='Email',
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылок'

    def __str__(self):
        return self.email


class Mailing(models.Model):
    start_time = models.DateTimeField(
        verbose_name='С какого момента рассылка может быть запущена',
        help_text="Введите дату и время запуска рассылки 'YYYY-MM-DD HH:MM:SS'",
        null=True,
        blank=True,
    )
    end_time = models.DateTimeField(
        verbose_name='До какого момента разрешено отправлять рассылку',
        help_text="Введите дату и время окончания запуска рассылки 'YYYY-MM-DD HH:MM:SS'",
        null=True,
        blank=True,
    )

    class Status(models.TextChoices):
        CREATE = 'create', 'Создана'
        SEND = 'send', 'Запущена'
        COMPLETED = 'completed', 'Завершена'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        verbose_name='Статус отправки',
        help_text="Выберите состояние письма",
    )
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(RecipientMail)

    def clean(self):
        """ Валидация даты рассылок. """
        super().clean()

        # Проверяем, что оба поля заполнены, чтобы избежать ошибок AttributeError
        if self.start_time and self.end_time:
            # Проверка: start_time не может быть в прошлом
            if self.start_time < timezone.now():
                raise ValidationError(
                    {"start_time": "Время начала рассылки не может быть в прошлом."}
                )

            # Проверка: start_time должен быть раньше end_time
            if self.start_time >= self.end_time:
                raise ValidationError(
                    {
                        "end_time": "Время окончания должно быть позже времени начала."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # ← пересчёт и сохранение статуса
        return obj

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class MailingAttempt(models.Model):
    # Статусы попытки в виде кортежа для поля выбора (Choices)
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    ]

    # Дата и время попытки
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки"
    )

    # Статус попытки
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Статус"
    )

    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ почтового сервера"
    )

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Рассылка"
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ['-attempt_time']  # Свежие попытки будут вверху

    def __str__(self):
        return f"Попытка для {self.mailing.id} ({self.status}) от {self.attempt_time.strftime('%d.%m.%Y %H:%M')}"
