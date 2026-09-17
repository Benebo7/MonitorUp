from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user: str
    password: str
    email: str = Field(unique=True)
    is_verified: bool = Field(default=False)
    monitors: list["Monitor"] = Relationship(back_populates="user")


class Monitor(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    name: str
    url: str
    status_code: int
    last_checked: Optional[str] = None
    user: list["User"] = Relationship(back_populates="monitors")
