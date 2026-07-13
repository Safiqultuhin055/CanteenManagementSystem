#!/bin/bash
set -euo pipefail

PORT="${CMS_PORT:-365}"

cd /app

echo "=== CanteenSys (Docker) ==="
echo "Port: ${PORT}"
echo "DB: ${DB_HOST}:${DB_PORT:-1433}/${DB_NAME}"

python deploy/docker/wait_for_db.py

echo "Applying idempotent schema patches…"
python deploy/docker/apply_schema_patches.py || true

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py sync_menu_permissions 2>/dev/null || true
python manage.py ensure_user_permissions_table 2>/dev/null || true
python manage.py seed_menu_item_images 2>/dev/null || true

echo "Starting Waitress on 0.0.0.0:${PORT} …"
exec python manage.py publish --serve --bind "0.0.0.0:${PORT}" \
  --skip-migrate --skip-static --skip-permissions
