from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv(override=True)

REDIS_URL = os.getenv("REDIS_URL")
REDIS_BACKEND_URL = os.getenv("REDIS_BACKEND_URL")
celery_app = Celery(
    "app",
    broker=REDIS_URL,
    backend=REDIS_BACKEND_URL,
)

# ✅ CORRECT
celery_app.autodiscover_tasks(["app.tasks.document_processing_task"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
