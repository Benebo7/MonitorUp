#!/usr/bin/env bash
set -euo pipefail

ssh -o StrictHostKeyChecking=no azureuser@158.23.16.113 'bash -s' << 'EOF'

set -euo pipefail

cd ~/MonitorUp
git fetch origin
git reset --hard origin/main
docker compose down
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml up -d
EOF