from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlmodel import Session, select

from models import Monitor
from core.security import is_url_safe

MAX_MONITORS_PER_USER = 5


class MonitorLimitReached(Exception):
    pass


class UnsafeUrl(Exception):
    pass


class MonitorNotFound(Exception):
    pass


def check_url_status(url: str) -> Optional[int]:
    try:
        return httpx.get(url, timeout=10).status_code
    except httpx.HTTPError:
        return None


def create_monitor(session: Session, user_id: UUID, name: str, url: str) -> Monitor:
    existing = session.exec(select(Monitor).where(Monitor.user_id == user_id)).all()
    if len(existing) >= MAX_MONITORS_PER_USER:
        raise MonitorLimitReached()
    if not is_url_safe(url):
        raise UnsafeUrl()

    monitor = Monitor(
        user_id=user_id,
        name=name,
        url=url,
        status_code=check_url_status(url) or 0,
        last_checked=datetime.now(timezone.utc).isoformat(),
    )
    session.add(monitor)
    session.commit()
    return monitor


def update_monitor(session: Session, monitor_id: UUID, user_id: UUID, name: str, url: str) -> Monitor:
    monitor = session.exec(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user_id)
    ).first()
    if not monitor:
        raise MonitorNotFound()
    if not is_url_safe(url):
        raise UnsafeUrl()

    monitor.name = name
    monitor.url = url
    monitor.status_code = check_url_status(url) or 0
    monitor.last_checked = datetime.now(timezone.utc).isoformat()
    session.add(monitor)
    session.commit()
    session.refresh(monitor)
    return monitor


def delete_monitor(session: Session, monitor_id: UUID, user_id: UUID) -> None:
    monitor = session.exec(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user_id)
    ).first()
    if not monitor:
        raise MonitorNotFound()
    session.delete(monitor)
    session.commit()
