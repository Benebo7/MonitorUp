from celery import Celery
import os
from dotenv import load_dotenv


load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
celery_app = Celery("tasks", broker=REDIS_URL,backend=REDIS_URL, include=["Services.monitor"])


celery_app.conf.beat_schedule = {
    "check-sites-every-minute": {
        "task": "Services.monitor.check_sites",
        "schedule": 60.0,
    }
}