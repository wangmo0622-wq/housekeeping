#!/bin/sh
set -e
cd /app
mkdir -p logs media
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear 2>/dev/null || true
exec "$@"
