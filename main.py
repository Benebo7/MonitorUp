from fastapi import FastAPI
from routers import auth, calc, monitor
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from dotenv import load_dotenv
import os
from database import create_db
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from Services.monitor import check_sites
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

scheduler = BackgroundScheduler()
@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(check_sites, "interval", seconds=60)
    scheduler.start()
@app.on_event("shutdown")
def shutdown_scheduler():    
    scheduler.shutdown()

create_db()
app.include_router(auth.router)
app.include_router(calc.router)
app.include_router(monitor.router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/dist/index.html")

# Serve all static assets (JS, CSS, images)
app.mount("/", StaticFiles(directory="frontend/dist"), name="static")
