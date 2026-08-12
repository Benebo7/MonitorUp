from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session, select
from security import checkuser, is_url_safe
import httpx
from database import get_session, Monitor
from limiter import limiter
from datetime import datetime, timezone
router = APIRouter(prefix="/monitor", tags=["Monitor"])
class MonitorInput(BaseModel):
    url: str
    name: str

@router.post("/create")
@limiter.limit("5/minute")
def create_monitor(request: Request, data: MonitorInput, id: str = Depends(checkuser), session = Depends(get_session)):
    #if user has more than 5 monitors, return error
    monitor_count = session.exec(select(Monitor).where(Monitor.user_id == UUID(id))).all()
    if len(monitor_count) >= 5:
        raise HTTPException(status_code=400, detail="You can only have 5 monitors")
    if not is_url_safe(data.url):
        raise HTTPException(status_code=400, detail="This URL is not allowed")
    try:
        response = httpx.get(data.url, timeout=10)
        initial_status = response.status_code
    except httpx.HTTPError:
        initial_status = 0

    new_monitor = Monitor(
        user_id=UUID(id),
        name=data.name,
        url=data.url,
        status_code=initial_status,
        last_checked= datetime.now(timezone.utc).isoformat()
    )

    session.add(new_monitor)
    session.commit()
    return {"message": "Monitor created successfully", "initial_status": initial_status, "monitor": new_monitor.name}


@router.get("/read")
@limiter.limit("3/minute")
def read_monitors(request: Request, id: str = Depends(checkuser), session = Depends(get_session)):
    monitors = session.exec(select(Monitor).where(Monitor.user_id == UUID(id))).all()
    
    return monitors

@router.delete("/delete/{monitor_id}")
@limiter.limit("5/minute")
def delete_monitor(request: Request, monitor_id: UUID, id: str = Depends(checkuser), session = Depends(get_session)):
    monitor = session.exec(select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == UUID(id))).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    session.delete(monitor)
    session.commit()
    return {"message": "Monitor deleted successfully"}

@router.put("/update/{monitor_id}")
@limiter.limit("5/minute")
def update_monitor(request: Request, monitor_id: UUID, data: MonitorInput, id: str = Depends(checkuser), session = Depends(get_session)):
    monitor = session.exec(select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == UUID(id))).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    if not is_url_safe(data.url):
        raise HTTPException(status_code=400, detail="This URL is not allowed")
    try:
        response = httpx.get(data.url, timeout=10)
        initial_status = response.status_code
    except httpx.HTTPError:
        initial_status = 0
    monitor.name = data.name
    monitor.url = data.url
    monitor.status_code = initial_status
    monitor.last_checked = datetime.now(timezone.utc).isoformat()
    session.add(monitor)
    session.commit()
    session.refresh(monitor)
    
    return {"message": "Monitor updated successfully"}, 