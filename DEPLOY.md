# Deploy do MonitorUp (VPS + nginx + SSL)

Guia para subir o projeto numa VPS Ubuntu com nginx como reverse proxy e HTTPS via Let's Encrypt.

Arquitetura final:

```
Internet -> nginx (80/443, SSL) -> uvicorn (127.0.0.1:8000) -> Postgres + Redis (rede interna do Docker)
```

## Pré-requisitos

- Uma VPS com Ubuntu (Hetzner, DigitalOcean, Contabo, etc.).
- Um domínio com um registro DNS `A` apontando para o IP da VPS.
- Acesso SSH como root (ou um usuário com sudo).

## 1. Setup inicial do servidor

```bash
# como root, crie um usuário não-root
adduser deploy
usermod -aG sudo deploy

# copie sua chave SSH para o novo usuário e passe a usar ele
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Daqui em diante, conecte como `deploy`.

## 2. Firewall (ufw) — só expõe o necessário

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH        # porta 22
sudo ufw allow 80/tcp         # nginx HTTP
sudo ufw allow 443/tcp        # nginx HTTPS
sudo ufw enable
sudo ufw status
```

Repare: **não** abrimos 8000 (uvicorn), 5432 (Postgres) nem 6379 (Redis). O uvicorn fica preso em `127.0.0.1` e banco/Redis vivem só na rede interna do Docker.

## 3. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
# saia e entre de novo no SSH para o grupo docker valer
```

## 4. Subir o código e configurar o `.env`

```bash
git clone <seu-repo> monitorup
cd monitorup
cp .env.example .env
nano .env
```

No `.env` de produção, ajuste:

- `SECRET_KEY` — gere um forte: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
- `POSTGRES_PASSWORD` — senha forte de verdade (não `senha`).
- `ORIGINS` — o domínio real, ex: `["https://monitorup.example.com"]` (não `["*"]` em prod).
- `DATABASE_URL` — pode deixar como está; o compose sobrescreve com o host interno `database_psgrts`.
- `REDIS_URL=redis://redis_cache:6379/0`

## 5. Buildar e rodar

```bash
docker build -t monitorup-api:latest .
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Rodar as migrations do Alembic (uma vez, e a cada novo deploy com mudança de schema):

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Teste local na VPS (deve responder, já que está em 127.0.0.1:8000):

```bash
curl -I http://127.0.0.1:8000
```

## 6. nginx no host

```bash
sudo apt update && sudo apt install -y nginx
sudo cp deploy/nginx/monitorup.conf /etc/nginx/sites-available/monitorup.conf
# troque "monitorup.example.com" pelo seu domínio dentro do arquivo
sudo nano /etc/nginx/sites-available/monitorup.conf
sudo ln -s /etc/nginx/sites-available/monitorup.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t        # testa a config
sudo systemctl reload nginx
```

Nesse ponto, `http://seu-dominio.com` já deve servir a aplicação.

## 7. SSL com Let's Encrypt (Certbot)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d monitorup.example.com
```

O Certbot edita o arquivo do nginx sozinho: adiciona o bloco `listen 443 ssl`, os certificados e o redirect de HTTP para HTTPS. A renovação automática já vem configurada (`systemctl status certbot.timer`).

## 8. Checklist final de produção

- [ ] `SECRET_KEY` e `POSTGRES_PASSWORD` fortes no `.env`.
- [ ] `ORIGINS` com o domínio real (sem `*`).
- [ ] Cookies de refresh com `secure=True` (hoje estão `secure=False` em `routers/auth.py`) — necessário porque agora é HTTPS.
- [ ] `echo=True` removido do `create_engine` em `database.py` para não logar todo SQL.
- [ ] Firewall ativo (`sudo ufw status`).
- [ ] WebSocket testado em produção (a config do nginx já faz o upgrade de conexão).

## Notas

- O rate limiter (`slowapi`) usa o IP do cliente. Atrás do nginx, o IP real chega via header `X-Forwarded-For`. Por isso o uvicorn roda com `--proxy-headers --forwarded-allow-ips=*` no `docker-compose.prod.yml`, e o nginx envia `X-Forwarded-For`. Sem isso, o limiter contaria todo mundo como o mesmo IP.
- O frontend hoje é servido pelo próprio uvicorn (`StaticFiles`). Funciona, mas se quiser otimizar depois, dá para o nginx servir o `frontend/dist` direto (mais rápido e tira carga da app).
