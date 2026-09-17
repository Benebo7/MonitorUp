from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import select

from core.security import checkuser
from core.database import get_session
from models import Monitor
from core.limiter import limiter
from services import monitor_service

router = APIRouter(prefix="/monitor", tags=["Monitor"])


class MonitorInput(BaseModel):
    url: str
    name: str


@router.post("/create")
@limiter.limit("5/minute")
def create_monitor(request: Request, data: MonitorInput, id: str = Depends(checkuser), session=Depends(get_session)):
    try:
        monitor = monitor_service.create_monitor(session, UUID(id), data.name, data.url)
    except monitor_service.MonitorLimitReached:
        raise HTTPException(status_code=400, detail="You can only have 5 monitors")
    except monitor_service.UnsafeUrl:
        raise HTTPException(status_code=400, detail="This URL is not allowed")

    return {"message": "Monitor created successfully", "initial_status": monitor.status_code, "monitor": monitor.name}


@router.get("/read")
@limiter.limit("3/minute")
def read_monitors(request: Request, id: str = Depends(checkuser), session=Depends(get_session)):
    monitors = session.exec(select(Monitor).where(Monitor.user_id == UUID(id))).all()
    return monitors


@router.delete("/delete/{monitor_id}")
@limiter.limit("5/minute")
def delete_monitor(request: Request, monitor_id: UUID, id: str = Depends(checkuser), session=Depends(get_session)):
    try:
        monitor_service.delete_monitor(session, monitor_id, UUID(id))
    except monitor_service.MonitorNotFound:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"message": "Monitor deleted successfully"}


@router.put("/update/{monitor_id}")
@limiter.limit("5/minute")
def update_monitor(request: Request, monitor_id: UUID, data: MonitorInput, id: str = Depends(checkuser), session=Depends(get_session)):
    try:
        monitor_service.update_monitor(session, monitor_id, UUID(id), data.name, data.url)
    except monitor_service.MonitorNotFound:
        raise HTTPException(status_code=404, detail="Monitor not found")
    except monitor_service.UnsafeUrl:
        raise HTTPException(status_code=400, detail="This URL is not allowed")

    return {"message": "Monitor updated successfully"}
