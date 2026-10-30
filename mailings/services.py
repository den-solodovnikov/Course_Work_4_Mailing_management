import smtplib

from django.core.mail import send_mail
from django.utils import timezone

from .models import Message, Mailing, MailingAttempt


def send_mailing_service(mailing: Mailing) -> None:
    now = timezone.now()

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError("Рассылка недоступна для отправки")

    attempts = []

    for recipient in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.title,
                message=mailing.message.content,
                from_email=None,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    attempt_time=timezone.now(),
                    status="Успешно",
                    server_response="Успешно",
                )
            )

        except Exception as exc:
            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    attempt_time=timezone.now(),
                    status="Не успешно",
                    server_response=f'Не успешно: {str(exc)}',
                )
            )

    MailingAttempt.objects.bulk_create(attempts)


def log_mailing_attempt(mailing, recipient_list):
    try:
        # Пример отправки сообщения
        send_mail(
            subject=mailing.subject,
            message=mailing.body,
            from_email='info@your-app.com',
            recipient_list=recipient_list,
            fail_silently=False,
        )

        # Если исключений не возникло — успех
        MailingAttempt.objects.create(
            mailing=mailing,
            status='Успешно',
            server_response='250 OK: Message accepted for delivery'
        )

    except smtplib.SMTPException as e:
        # Ловим специфичные ошибки почтового сервера
        MailingAttempt.objects.create(
            mailing=mailing,
            status='Не успешно',
            server_response=f"SMTP Error: {str(e)}"
        )
    except Exception as e:
        # Ловим любые другие системные ошибки (нет сети и т.д.)
        MailingAttempt.objects.create(
            mailing=mailing,
            status='Не успешно',
            server_response=f"General Error: {str(e)}"
        )
