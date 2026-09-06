"""Celery worker application initialization."""

from celery import Celery
from core.config import settings

celery_app = Celery(
    "amip_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 min max
)
