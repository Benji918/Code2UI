"""
Celery configuration for Code2UI background tasks.
"""
from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Redis URL for broker and result backend
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery instance
celery_app = Celery(
    'code2ui',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['services.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    result_expires=3600,  # Results expire after 1 hour
)

if __name__ == '__main__':
    celery_app.start()
