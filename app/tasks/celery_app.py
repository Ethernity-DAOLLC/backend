from celery import Celery
from celery.schedules import crontab
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "ethernity_dao",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    'sync-blockchain-events': {
        'task': 'app.tasks.blockchain_tasks.sync_blockchain_events',
        'schedule': 30.0,
    },

    'process-pending-events': {
        'task': 'app.tasks.blockchain_tasks.process_pending_events',
        'schedule': 60.0,
    },

    'send-burn-warnings': {
        'task': 'app.tasks.notification_tasks.send_token_burn_warnings',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },

    'check-retirement-ready': {
        'task': 'app.tasks.notification_tasks.send_retirement_ready_notifications',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
    },

    'create-daily-snapshot': {
        'task': 'app.tasks.analytics_tasks.create_daily_snapshot',
        'schedule': crontab(hour=0, minute=5),  # Daily at 00:05
    },
}

logger.info("✅ Celery app configured")
