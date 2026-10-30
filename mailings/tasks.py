from celery import shared_task
from django.core.management import call_command
from django.utils import timezone

from mailings.models import Mailing
from mailings.services import send_mailing_service


@shared_task
def check_and_run_mailings_task():
    """
    Периодическая задача: ищет активные по времени рассылки
    и отправляет их в очередь на выполнение.
    """
    now = timezone.now()

    # Фильтруем рассылки, которые актуальны прямо сейчас
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now
    ).exclude(status=Mailing.Status.COMPLETED)

    for mailing in active_mailings:
        mailing.status = Mailing.Status.SEND
        mailing.save(update_fields=['status'])
        # Вызываем задачу асинхронно через .delay()
        send_single_mailing_task.delay(mailing.id)


@shared_task
def send_single_mailing_task(mailing_id):
    """
    Асинхронная задача для обработки конкретной рассылки по её ID.
    """
    try:
        mailing = Mailing.objects.get(pk=mailing_id)
        # Вызываем ранее написанный сервис с бизнес-логикой
        success, message = send_mailing_service(mailing)
        if success:
            mailing.status = Mailing.Status.COMPLETED
        else:
            mailing.status = Mailing.Status.CREATE  # возвращаем в исходный при ошибке
        mailing.save(update_fields=['status'])
        return f"Mailing {mailing_id}: {message}"

    except Mailing.DoesNotExist:
        return f"Mailing {mailing_id} not found."