from datetime import datetime
import os
import json
from core.logger import logger
import redis
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from uuid import UUID

from core.database import engine
from models import Monitor
from core.security import is_url_safe
from email_utils import send_email
from celery_app import celery_app
from services.monitor_service import check_url_status

BATCH_SIZE = 50
redis_client = redis.from_url(os.getenv("REDIS_URL"))


@celery_app.task
def dispatch_checks():
    with Session(engine) as session:
        ids = [str(uid) for uid in session.exec(select(Monitor.id)).all()]
        for i in range(0, len(ids), BATCH_SIZE):
            check_batch.delay(ids[i:i + BATCH_SIZE])


@celery_app.task
def check_batch(monitor_ids):
    with Session(engine) as session:
        monitors = session.exec(
            select(Monitor)
            .where(Monitor.id.in_([UUID(i) for i in monitor_ids])).options(joinedload(Monitor.user))).all()
        for m in monitors:
            if not is_url_safe(m.url):
                session.delete(m)
                continue

            m.last_checked = datetime.utcnow().isoformat()
            new_status = check_url_status(m.url)
            if new_status is not None:
                redis_client.publish("monitor_updates", json.dumps({
                    "user_id": str(m.user_id),
                    "monitor_id": str(m.id),
                    "status_code": new_status,
                    "last_checked": m.last_checked,
                }))

            if m.status_code != new_status and m.status_code is not None:
                m.status_code = new_status
                user = m.user
                if user:
                    try:
                        send_email(m.url, new_status, user.email)
                    except Exception as e:
                        logger.error(f"Error sending email: {e}")

            m.status_code = new_status

        session.commit()
