from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import auth, monitor
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import WebSocket
from websocket import websocket_endpoint

load_dotenv()



@asynccontextmanager
async def lifespan(app: FastAPI):
    
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
origins = os.getenv("ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(monitor.router)
@app.websocket("/ws/{token}")
async def ws_route(websocket: WebSocket, token: str):
    await websocket_endpoint(websocket, token)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/dist/index.html")

app.mount("/", StaticFiles(directory="frontend/dist"), name="static")


