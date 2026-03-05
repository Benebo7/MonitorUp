
from database import get_session, Monitor, User
import httpx
from datetime import datetime
from sqlmodel import update, select
import asyncio
from websocket import connections
from email_utils import send_email

def check_sites():
    session = next(get_session())   
    
    statement = select(Monitor)
    monitor = session.exec(statement).all()  
    for m in monitor:
        try:
            response = httpx.get(m.url, timeout=10)
            new_status = response.status_code
            m.last_checked = datetime.utcnow().isoformat()
            if m.user_id in connections:
                ws = connections[m.user_id]
                try:
                    asyncio.run(ws.send_json({"monitor_id": str(m.id), "status_code": new_status, "last_checked": m.last_checked}))
                except:
                    connections.pop(m.user_id, None)
            
        except Exception as e:
            new_status = None  
        
        if m.status_code != new_status and m.status_code is not None:
            m.status_code = new_status
            user = session.exec(select(User).where(User.id == m.user_id)).first()
            if user:
                try:
                    send_email(m.url, new_status, user.email)
                except:
                    pass

        session.execute(update(Monitor).where(Monitor.id == m.id).values(status_code=new_status, last_checked=m.last_checked))
    session.commit()


    