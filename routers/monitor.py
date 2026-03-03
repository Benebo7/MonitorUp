from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from security import checkuser
import httpx
from database import get_session, Monitor
from limiter import limiter

router = APIRouter(prefix="/monitor", tags=["Monitor"])
class MonitorInput(BaseModel):
    url: str
    name: str

@router.post("/create")
@limiter.limit("5/minute")
def create_monitor(request: Request, data: MonitorInput, id: str = Depends(checkuser), session = Depends(get_session)):
    #if user has more than 5 monitors, return error
    
    try:
        response = httpx.get(data.url, timeout=10)
        initial_status = response.status_code
    except:
        initial_status = 0

    new_monitor = Monitor(
        user_id=int(id),
        name=data.name,
        url=data.url,
        status_code=initial_status,
        last_checked=datetime.utcnow().isoformat()
    )
    session.add(new_monitor)
    session.commit()
    return {"message": "Monitor created successfully", "initial_status": initial_status}


@router.get("/read")
@limiter.limit("3/minute")
def read_monitors(request: Request, id: str = Depends(checkuser), session = Depends(get_session)):
    monitors = session.exec(select(Monitor).where(Monitor.user_id == int(id))).all()
    return monitors

@router.delete("/delete/{monitor_id}")
@limiter.limit("5/minute")
def delete_monitor(request: Request, monitor_id: int, id: str = Depends(checkuser), session = Depends(get_session)):
    monitor = session.exec(select(Monitor).where(Monitor.id == monitor_id)).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    session.delete(monitor)
    session.commit()
    return {"message": "Monitor deleted successfully"}

@router.put("/update/{monitor_id}")
@limiter.limit("5/minute")
def update_monitor(request: Request, monitor_id: int, data: MonitorInput, id: str = Depends(checkuser), session = Depends(get_session)):
    monitor = session.exec(select(Monitor).where(Monitor.id == monitor_id)).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    monitor.name = data.name
    monitor.url = data.url
    session.add(monitor)
    session.commit()
    return {"message": "Monitor updated successfully"}