from typing import Optional, Generator
from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from security import get_password_hash, verify_password
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Define it in your .env file.")

class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user: str = Field(unique=True)
    password: str
    email: str = Field(unique=True)

class Monitor(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    name: str
    url: str
    status_code: int
    last_checked: Optional[str] = None


engine = create_engine(DATABASE_URL, echo=False)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    create_db()
