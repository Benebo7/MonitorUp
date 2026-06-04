from database import get_session, Monitor, User
import httpx
from datetime import datetime
from sqlmodel import update, select
import asyncio
from uuid import UUID
from websocket import connections
from email_utils import send_email
from celery_app import celery_app

BATCH_SIZE = 50


@celery_app.task
def dispatch_checks():
    session = next(get_session())
    ids = [str(uid) for uid in session.exec(select(Monitor.id)).all()]
    for i in range(0, len(ids), BATCH_SIZE):
        check_batch.delay(ids[i:i + BATCH_SIZE])


@celery_app.task
def check_batch(monitor_ids):
    session = next(get_session())
    monitors = session.exec(
        select(Monitor).where(Monitor.id.in_([UUID(i) for i in monitor_ids]))
    ).all()
    for m in monitors:
        try:
            response = httpx.get(m.url, timeout=10)
            new_status = response.status_code
            m.last_checked = datetime.utcnow().isoformat()
            if str(m.user_id) in connections:
                ws = connections[str(m.user_id)]
                try:
                    asyncio.run(ws.send_json({"monitor_id": str(m.id), "status_code": new_status, "last_checked": m.last_checked}))
                except Exception:
                    connections.pop(str(m.user_id), None)
        except Exception:
            new_status = None

        if m.status_code != new_status and m.status_code is not None:
            m.status_code = new_status
            user = session.exec(select(User).where(User.id == m.user_id)).first()
            if user:
                try:
                    send_email(m.url, new_status, user.email)
                except Exception:
                    pass

        session.execute(update(Monitor).where(Monitor.id == m.id).values(status_code=new_status, last_checked=m.last_checked))
    session.commit()
