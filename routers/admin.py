import os
from fastapi import APIRouter, Request, HTTPException, Cookie, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select, func, SQLModel
from typing import Optional
from fastapi import Query
from limiter import limiter
from database import get_session, User, Monitor
from dotenv import load_dotenv
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime
from security import checkadmin
from classes.MoniUser import UserMonitors, MonitorUser
router = APIRouter(prefix="/admin", tags=["Admin"])

load_dotenv()

class token(BaseModel):
    token: str

@router.post("/verify")
@limiter.limit("5/minute")
def admin_auth(request: Request, token: token):
    
    checkadmin(token.token)
    response = JSONResponse(content={"message": "Admin access granted"})
    response.set_cookie(
    key="admin_token",
    value=token.token,
    httponly=True,
    samesite="lax",
    secure=True,
    path="/admin",
     max_age=1800
    )
    return response
    
class PaginatedUsers(BaseModel):
    users: list[UserMonitors]
    page: int
    page_size: int
    total_users: int

@router.get("/users", response_model=PaginatedUsers)
@limiter.limit("5/minute")
def get_users(request: Request, admin_token: str = Cookie(default=None), session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    monitors_qtt: Optional[int] = Query(None, description="Filter by number of monitors")

    ):
    checkadmin(admin_token)

    offset = (page - 1) * page_size
    limit = page_size

    stmt = select(User)
    stmt_count = select(func.count()).select_from(User)
    if is_verified is not None:
        stmt = stmt.where(User.is_verified == is_verified)
        stmt_count = stmt_count.where(User.is_verified == is_verified)
    if monitors_qtt is not None:                                                            
        stmt = stmt.join(User.monitors).group_by(User.id).having(func.count(Monitor.id) >= monitors_qtt)
        stmt_count = stmt_count.join(User.monitors).group_by(User.id).having(func.count(Monitor.id) >= monitors_qtt)
    
    statement = stmt.offset(offset).limit(limit).options(selectinload(User.monitors))
    users = session.exec(statement).all() 

    total = session.exec(stmt_count).first()

    return {"users": users, "page": page, "page_size": page_size, "total_users": total}

class PaginatedMonitors(BaseModel):
    monitors: list[MonitorUser]
    page: int
    page_size: int
    total_monitors: int
    
@router.get("/monitors", response_model=PaginatedMonitors)
@limiter.limit("5/minute")
def get_monitors(request: Request, admin_token: str = Cookie(default=None), session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    statuscode: Optional[int] = Query(None, description="Filter by status code"),
    last_checked: Optional[str] = Query(None, description="Filter by last checked date"),
    lc_mode: Optional[str] = Query(None, description="Filter mode for last_checked: 'before', 'after', or 'on'")
    ):
    offset = (page - 1) * page_size
    limit = page_size
    checkadmin(admin_token)

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
            raise HTTPException(status_code=400, detail="Invalid lc_mode. Use 'before', 'after', or 'on'.")
        

    statement = stmt.offset(offset).limit(limit).options(joinedload(Monitor.user))
    monitors = session.exec(statement).all()
    total = session.exec(stmt_count).first()
    
    return {"monitors": monitors, "page": page, "page_size": page_size, "total_monitors": total}



    