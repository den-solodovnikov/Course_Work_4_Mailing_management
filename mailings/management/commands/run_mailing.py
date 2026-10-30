from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from config import settings
from mailings.models import Mailing, MailingAttempt
from mailings.tasks import send_single_mailing_task


class Command(BaseCommand):
    help = 'Отправка фоновых рассылок по расписанию или требованию по её ID'

    def add_arguments(self, parser):
        # Принимаем ID рассылки как обязательный аргумент
        parser.add_argument('mailing_id', type=int, nargs='?', default=0)

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        # Вместо прямой отправки — делегируем задачу Celery воркеру
        send_single_mailing_task.delay(mailing_id)

        self.stdout.write(self.style.SUCCESS(
            f"Рассылка {mailing_id} успешно поставлена в очередь Celery."
        ))
        
        # try:
        #     mailing = Mailing.objects.get(pk=mailing_id)
        # except Mailing.DoesNotExist:
        #     raise CommandError(f"Рассылка с ID {mailing_id} не найдена.")
        #
        # now = timezone.now()
        # print(f'{mailing.start_time}<<<<<{now}<<<<<{mailing.end_time}')
        #
        # if not mailing.start_time <= now <= mailing.end_time:
        #     raise ValueError("Рассылка недоступна для отправки")
        #
        # attempts = []
        # recipients_email = mailing.recipients.all()
        # self.stdout.write(f'Начало рассылки для ID: {mailing.id}...')
        #
        # for recipient in recipients_email:
        #     try:
        #         send_mail(
        #             subject=mailing.message.title,
        #             message=mailing.message.content,
        #             from_email=settings.DEFAULT_FROM_EMAIL,
        #             recipient_list=[recipient.email],
        #             fail_silently=False,
        #         )
        #
        #         attempts.append(
        #             MailingAttempt(
        #                 mailing=mailing,
        #                 attempt_time=timezone.now(),
        #                 status="Успешно",
        #                 server_response="Письмо отправлено",
        #             )
        #         )
        #
        #     except Exception as exc:
        #         attempts.append(
        #             MailingAttempt(
        #                 mailing=mailing,
        #                 attempt_time=timezone.now(),
        #                 status="Не успешно",
        #                 server_response=str(exc),
        #             )
        #         )
        #         self.stdout.write(self.style.SUCCESS(f'Рассылка {mailing} успешно завершена!'))
        #     except Exception as e:
        #         self.stdout.write(self.style.ERROR(f'Ошибка при отправке: {str(e)}'))
        #
        # MailingAttempt.objects.bulk_create(attempts)
        # ------------------------------------------------------------

        # # Вызов сервисной функции
        # result = send_mailing(mailing)
        #
        # if result['success']:
        #     self.stdout.write(self.style.SUCCESS(result['message']))
        # else:
        #     self.stdout.write(self.style.ERROR(result['message']))
