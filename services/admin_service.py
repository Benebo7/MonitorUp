from typing import Optional

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, func, select

from models import Monitor, User


class InvalidFilterMode(Exception):
    pass


def list_users(
    session: Session,
    page: int,
    page_size: int,
    is_verified: Optional[bool] = None,
    monitors_qtt: Optional[int] = None,
) -> tuple[list[User], int]:
    offset = (page - 1) * page_size

    stmt = select(User)
    stmt_count = select(func.count()).select_from(User)
    if is_verified is not None:
        stmt = stmt.where(User.is_verified == is_verified)
        stmt_count = stmt_count.where(User.is_verified == is_verified)
    if monitors_qtt is not None:
        stmt = stmt.join(User.monitors).group_by(User.id).having(func.count(Monitor.id) >= monitors_qtt)
        stmt_count = stmt_count.join(User.monitors).group_by(User.id).having(func.count(Monitor.id) >= monitors_qtt)

    statement = stmt.offset(offset).limit(page_size).options(selectinload(User.monitors))
    users = session.exec(statement).all()
    total = session.exec(stmt_count).first()

    return users, total


def list_monitors(
    session: Session,
    page: int,
    page_size: int,
    statuscode: Optional[int] = None,
    last_checked: Optional[str] = None,
    lc_mode: Optional[str] = None,
) -> tuple[list[Monitor], int]:
    offset = (page - 1) * page_size

    stmt = select(Monitor)
    stmt_count = select(func.count()).select_from(Monitor)
    if statuscode is not None:
        stmt = stmt.where((Monitor.status_code // 100) == statuscode)
        stmt_count = stmt_count.where((Monitor.status_code // 100) == statuscode)
    if last_checked is not None:
        if lc_mode == "before":
            stmt = stmt.where(Monitor.last_checked < last_checked)
            stmt_count = stmt_count.where(Monitor.last_checked < last_checked)
        elif lc_mode == "after":
            stmt = stmt.where(Monitor.last_checked > last_checked)
            stmt_count = stmt_count.where(Monitor.last_checked > last_checked)
        elif lc_mode == "on":
            stmt = stmt.where(Monitor.last_checked == last_checked)
            stmt_count = stmt_count.where(Monitor.last_checked == last_checked)
        else:
            raise InvalidFilterMode()

    statement = stmt.offset(offset).limit(page_size).options(joinedload(Monitor.user))
    monitors = session.exec(statement).all()
    total = session.exec(stmt_count).first()

    return monitors, total
