
from database import get_session, Monitor
import httpx
from datetime import datetime
from fastapi import HTTPException
from sqlmodel import update
#from email_utils import send_email

def check_sites():
    session = next(get_session())   
    
    statement = select(Monitor)
    monitor = session.exec(statement).all()  
    for m in monitor:
        try:
            response = httpx.get(m.url, timeout=10)
            new_status = response.status_code
            m.last_checked = datetime.utcnow().isoformat()
            
        except Exception as e:
            new_status = None  
        
        if m.status_code != new_status and m.status_code is not None:

            m.status_code = new_status


            
            
            send_email(m.url, new_status)

        
        
        session.execute(update(Monitor).where(Monitor.id == m.id).values(status_code=new_status, last_checked=m.last_checked))  
            
    # 1. get all monitors from DB
    # 2. fetch each URL
    # 3. compare old status vs new status
    # 4. if changed → update DB, send email
    # 5. update last_checked


    