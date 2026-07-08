# MonitorUp

**Real-time website uptime monitoring — built to run in production.**

🔗 **Live:** [monitorup.me](https://monitorup.me)

MonitorUp lets you register URLs and watch their status in real time. A background scheduler pings every monitored site on an interval, pushes status changes to the browser over WebSockets the moment they happen, and emails you when something goes down or recovers.

This is a learning-driven project built end to end: from the FastAPI backend and React frontend down to the Docker images, the reverse proxy, the TLS certificates, and the CI/CD pipeline that ships it.

---
new line
## Features

- 🔐 **JWT authentication** — signup/login with short-lived access tokens + an httpOnly refresh-token cookie.
- 📋 **Monitor CRUD** — add, edit, list and delete the URLs you want to watch (scoped per user).
- ⏱️ **Periodic uptime checks** — a Celery Beat scheduler dispatches checks every 60s.
- ⚡ **Live status over WebSockets** — status changes reach the dashboard instantly via Redis Pub/Sub, no polling.
- 📧 **Email alerts** — get notified when a monitor's status code changes (down/recovered).
- 🛡️ **Rate limiting** — per-IP limits on auth and monitor endpoints.

---

## Architecture

```
                         ┌──────────────┐
   Browser  ──HTTPS──►   │    NGINX     │  reverse proxy + TLS termination
   (React)  ◄─WS──────   │  :80 / :443  │
                         └──────┬───────┘
                                │ 127.0.0.1:8000
                                ▼
                         ┌──────────────┐        ┌──────────────────┐
                         │   FastAPI    │◄──────►│  PostgreSQL      │
                         │  (uvicorn)   │        │  (managed/Aiven) │
                         └──────┬───────┘        └──────────────────┘
                                │ subscribe
                                ▼
        ┌───────────────────────────────────────────┐
        │                  Redis                     │
        │   broker (Celery queue)  +  Pub/Sub        │
        └───────▲───────────────────────┬───────────┘
                │ enqueue                │ publish status
        ┌───────┴───────┐       ┌────────┴────────┐
        │  Celery Beat  │       │  Celery Worker  │
        │  (scheduler)  │──────►│  pings URLs,    │
        │  every 60s    │ tasks │  emails alerts  │
        └───────────────┘       └─────────────────┘
```

**The check pipeline (fan-out):**
1. **Beat** fires `dispatch_checks` every 60s.
2. `dispatch_checks` reads all monitor IDs and **fans them out** into batches (`check_batch.delay(...)`), so checks run in parallel across workers instead of one giant task.
3. Each **worker** pings its batch of URLs with `httpx`, updates the DB, and **publishes** any change to a Redis Pub/Sub channel.
4. A FastAPI background subscriber receives those messages and **forwards them over WebSocket** to the right connected user — the dashboard updates live.
5. On a status change, the worker also sends an **email alert**.

---

## Tech stack

| Layer | Tech |
|---|---|
| **Backend** | FastAPI, SQLModel / SQLAlchemy 2.0, Pydantic |
| **Async tasks** | Celery (Beat + Workers), Redis (broker + Pub/Sub) |
| **Realtime** | WebSockets (Starlette) + Redis Pub/Sub |
| **Database** | PostgreSQL (managed), Alembic migrations |
| **Auth** | JWT (PyJWT), bcrypt password hashing |
| **Frontend** | React + Vite |
| **Infra** | Docker (multi-stage), Docker Compose, NGINX, Let's Encrypt |
| **CI/CD** | GitHub Actions (test → build → migrate → deploy) |
| **Tests** | pytest + FastAPI TestClient (SQLite in-memory) |

---

## Project structure

```
.
├── main.py                  # FastAPI app + lifespan (WebSocket subscriber)
├── database.py              # SQLModel models (User, Monitor) + engine/session
├── security.py              # password hashing, JWT, auth dependency
├── limiter.py               # slowapi rate limiter
├── websocket.py             # WS endpoint + Redis Pub/Sub subscriber
├── celery_app.py            # Celery app + beat schedule
├── email_utils.py           # email alerts
├── routers/
│   ├── auth.py              # signup / login / refresh
│   └── monitor.py           # monitor CRUD
├── Services/
│   └── monitor.py           # Celery tasks: dispatch_checks, check_batch
├── migrations/              # Alembic migrations
├── frontend/                # React + Vite app (built into static assets)
├── tests/                   # pytest suite (TestClient + SQLite)
├── deploy/                  # nginx config + k8s manifests
├── Dockerfile               # multi-stage: builds frontend, serves via FastAPI
├── docker-compose.prod.yml  # api + worker + beat + redis
└── .github/workflows/ci.yml # CI/CD pipeline
```

---

## How it's deployed

MonitorUp runs on a single DigitalOcean droplet, fronted by NGINX with a Let's Encrypt certificate:

- **Docker multi-stage build** — a Node stage compiles the React frontend; the Python stage serves the API and the built static assets from one image. The same image runs as three containers (`api`, `worker`, `beat`) via different commands.
- **NGINX** terminates TLS on `:443`, redirects `:80 → :443`, and reverse-proxies to the API on `127.0.0.1:8000` (with a dedicated `location` for WebSocket upgrades).
- **PostgreSQL** is a managed instance (durable data lives off-box); **Redis** runs as an ephemeral container (transient queue + Pub/Sub, nothing to persist).

### CI/CD

On every push to `main`, GitHub Actions:

1. **Tests** — spins up a clean runner, installs deps, runs the `pytest` suite. A failing test **blocks the deploy**.
2. **Deploys** — SSHes into the droplet and runs: `git pull → docker build → alembic upgrade head → docker compose up -d`. Migrations run before the new app comes up.

---

## Local development

> The app is live at [monitorup.me](https://monitorup.me) — running locally is optional.

```bash
# backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# set env vars: DATABASE_URL, REDIS_URL, SECRET_KEY, ALGORITHM, ORIGINS
alembic upgrade head
uvicorn main:app --reload

# frontend
cd frontend && npm install && npm run dev

# or the whole stack
docker compose up --build
```

### Tests

```bash
pytest
```

The suite uses an in-memory SQLite database swapped in via FastAPI's dependency overrides, so tests run fast and never touch a real database.


---

Built by [Benebo7](https://github.com/Benebo7) as a hands-on dive into backend engineering and DevOps.
