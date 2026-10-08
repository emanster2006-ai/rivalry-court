#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  cp .env.example .env
  if command -v openssl >/dev/null 2>&1; then
    jwt_secret="$(openssl rand -hex 32)"
    db_password="$(openssl rand -hex 24)"
    auth_password="$(openssl rand -hex 24)"
    sed -i.bak "s|AUTH_JWT_SECRET=replace-with-a-long-random-secret|AUTH_JWT_SECRET=$jwt_secret|; s|POSTGRES_PASSWORD=change-me|POSTGRES_PASSWORD=$db_password|; s|AUTH_DB_PASSWORD=change-me-too|AUTH_DB_PASSWORD=$auth_password|; s|rivalry:change-me@db|rivalry:$db_password@db|" .env
    rm .env.bak
  fi
fi
if docker compose version >/dev/null 2>&1; then
  docker compose up --build -d
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose up --build -d
else
  echo 'Docker Compose is required.' >&2
  exit 1
fi
echo 'Web: http://localhost:5173 | Mailpit: http://localhost:8025'
