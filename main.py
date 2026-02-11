from fastapi import FastAPI
from routers import auth, calc
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from dotenv import load_dotenv
import os
from database import create_db
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
origins = os.getenv("ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_db()
app.include_router(auth.router)
app.include_router(calc.router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
