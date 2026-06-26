from celery import Celery
import os
from dotenv import load_dotenv


load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
celery_app = Celery("tasks", broker=REDIS_URL,backend=REDIS_URL, include=["Services.monitor", "email_utils"])


celery_app.conf.beat_schedule = {
    "dispatch-checks-every-minute": {
        "task": "Services.monitor.dispatch_checks",
        "schedule": 60.0,
    }
}