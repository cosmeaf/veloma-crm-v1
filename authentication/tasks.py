# authentication/tasks.py
from celery import shared_task
from django.utils import timezone

@shared_task
def heartbeat():
    return f"beat at {timezone.now().isoformat()}"
