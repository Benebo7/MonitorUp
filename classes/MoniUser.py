from typing import Optional
from sqlmodel import SQLModel

class UserPublic(SQLModel):
    user: str
    email: str
    is_verified: bool

class MonitorPublic(SQLModel):
    name: str
    url: str
    status_code: int
    last_checked: Optional[str] = None  

class UserMonitors(SQLModel):
    user: str
    email: str
    is_verified: bool
    monitors: list[MonitorPublic] = []

class MonitorUser(SQLModel):
    name: str
    url: str
    status_code: int
    last_checked: Optional[str] = None
    user: UserPublic