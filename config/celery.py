import os
from celery import Celery

# Устанавливаем дефолтный модуль настроек Django для celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Используем строку конфигурации, чтобы воркеру не нужно было перезапускаться при изменении настроек celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в файлах tasks.py приложений Django
app.autodiscover_tasks()