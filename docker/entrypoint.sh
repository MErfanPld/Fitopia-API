#!/bin/sh
set -e

echo "[entrypoint] waiting for filesystem..."
mkdir -p /app/data /app/media /app/staticfiles

# Optional: wait for Redis if not optional
if [ "${REDIS_OPTIONAL:-true}" != "true" ] && [ -n "${REDIS_URL:-}" ]; then
  echo "[entrypoint] Redis required — checking..."
  # soft wait; app can still start if REDIS_OPTIONAL=true
  sleep 2
fi

echo "[entrypoint] migrate..."
python manage.py migrate --noinput

echo "[entrypoint] collectstatic..."
python manage.py collectstatic --noinput

echo "[entrypoint] starting: $*"
exec "$@"
