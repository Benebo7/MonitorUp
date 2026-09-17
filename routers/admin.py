import os
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from fastapi import Query
from dotenv import load_dotenv

from core.limiter import limiter
from core.database import get_session
from core.security import checkadmin
from schemas import UserMonitors, MonitorUser
from services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])

load_dotenv()

class token(BaseModel):
    token: str

@router.post("/verify")
@limiter.limit("5/minute")
def admin_auth(request: Request, token: token):

    if token.token != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=401, detail="Invalid admin token")
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

@router.get("/users", response_model=PaginatedUsers, dependencies=[Depends(checkadmin)])
@limiter.limit("5/minute")
def get_users(request: Request, session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    monitors_qtt: Optional[int] = Query(None, description="Filter by number of monitors")
    ):
    users, total = admin_service.list_users(session, page, page_size, is_verified, monitors_qtt)
    return {"users": users, "page": page, "page_size": page_size, "total_users": total}

class PaginatedMonitors(BaseModel):
    monitors: list[MonitorUser]
    page: int
    page_size: int
    total_monitors: int

@router.get("/monitors", response_model=PaginatedMonitors, dependencies=[Depends(checkadmin)])
@limiter.limit("5/minute")
def get_monitors(request: Request, session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    statuscode: Optional[int] = Query(None, description="Filter by status code"),
    last_checked: Optional[str] = Query(None, description="Filter by last checked date"),
    lc_mode: Optional[str] = Query(None, description="Filter mode for last_checked: 'before', 'after', or 'on'")
    ):
    try:
        monitors, total = admin_service.list_monitors(session, page, page_size, statuscode, last_checked, lc_mode)
    except admin_service.InvalidFilterMode:
        raise HTTPException(status_code=400, detail="Invalid lc_mode. Use 'before', 'after', or 'on'.")

    return {"monitors": monitors, "page": page, "page_size": page_size, "total_monitors": total}
