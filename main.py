from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from routers import auth, monitor, admin
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.limiter import limiter
from dotenv import load_dotenv
from uuid import uuid4
import os
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import WebSocket
from websocket import websocket_endpoint, redis_subscriber
from pathlib import Path
from core.database import create_db
from core.logger import logger
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    subscriber = asyncio.create_task(redis_subscriber())
    yield
    subscriber.cancel()

app = FastAPI(lifespan=lifespan)
origins = os.getenv("ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    request_id = str(uuid4())

    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    logger.info(
        f"{request.method} {request.url.path} completed_in={process_time:.2f}ms status_code={response.status_code} request_id={request_id}"
    )
    return response
@app.router.get("/health")
async def health_check():
    return {"status": "ok"}
app.include_router(auth.router)
app.include_router(monitor.router)
app.include_router(admin.router)
Instrumentator().instrument(app).expose(app)

@app.websocket("/ws/{token}")
async def ws_route(websocket: WebSocket, token: str):
    await websocket_endpoint(websocket, token)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/") 
async def serve_frontend():
    return FileResponse("frontend/dist/index.html")

# SPA fallback: the email link points at /verify, which is a frontend route.
# Serve index.html here so React boots and the Verify page reads ?token=.
@app.get("/verify")
async def serve_verify():
    return FileResponse("frontend/dist/index.html")

# SPA fallback: /admin is the frontend's admin panel route, not an API route
# (the admin router only defines /admin/verify, /admin/users, /admin/monitors).
@app.get("/admin")
async def serve_admin():
    return FileResponse("frontend/dist/index.html")

if Path("frontend/dist").exists():
    app.mount("/", StaticFiles(directory="frontend/dist"), name="static")

