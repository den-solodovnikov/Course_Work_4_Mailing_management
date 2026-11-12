import smtplib

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Mailing, MailingAttempt


def send_mailing_service(mailing: Mailing) -> tuple[bool, str]:

    recipients = mailing.recipients.all()
    if not recipients.exists():
        return False, "У рассылки нет получателей."

    now = timezone.now()

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError("Рассылка недоступна для отправки")

    if mailing.status == Mailing.Status.CREATED:
        mailing.status = Mailing.Status.STARTED
        mailing.save(update_fields=['status'])

    success_count = 0
    failed_count = 0
    last_error = ''

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            MailingAttempt.objects.create(
                mailing=mailing,
                status='status',
                server_response="Письмо успешно отправлено",
            )
            success_count += 1
        except (smtplib.SMTPException, Exception) as error:
            last_error = str(error)

            MailingAttempt.objects.create(
                mailing=mailing,
                status='failed',
                server_response=last_error,
            )
            failed_count += 1

    # Формируем итоговый ответ для Celery-задачи
    total = success_count + failed_count
    result_message = f"Обработано: {total}. Успешно: {success_count}, с ошибкой: {failed_count}."

    # Если ни одно письмо не ушло при наличии клиентов, считаем запуск неуспешным
    if success_count == 0 and failed_count > 0:
        return False, result_message

    return True, result_message

    #

def log_mailing_attempt(mailing, recipient_list):
    try:
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
