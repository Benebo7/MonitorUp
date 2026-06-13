# ---- Stage 1: build do frontend (Vite/React) ----
FROM node:20-slim AS frontend
WORKDIR /frontend

# Copia só os manifests primeiro (cache: só reinstala se as deps mudarem)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copia o resto do frontend e gera o build de produção em /frontend/dist
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend (FastAPI) ----
FROM python:3.10-slim

# Python não cria .pyc e loga na hora
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cache das deps Python: só reinstala se requirements.txt mudar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do backend
COPY . .

# Traz o dist já buildado do stage do frontend
COPY --from=frontend /frontend/dist ./frontend/dist

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
