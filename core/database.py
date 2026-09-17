from typing import Generator

from sqlmodel import Session, SQLModel, create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Define it in your .env file.")

engine = create_engine(DATABASE_URL, echo=False)

import models  # noqa: F401 - registers the tables on SQLModel.metadata before create_all()


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    create_db()
