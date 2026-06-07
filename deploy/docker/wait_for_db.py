"""Wait until Django can connect to SQL Server (Docker startup)."""
import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen_system.settings')

import django

django.setup()

from django.db import connection

deadline = int(os.environ.get('DB_WAIT_SECONDS', '120'))
interval = 2

for elapsed in range(0, deadline + 1, interval):
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        print('Database connection OK.')
        sys.exit(0)
    except Exception as exc:
        print(f'Waiting for database… ({elapsed}s) {exc}')
        time.sleep(interval)

print(f'Database not ready after {deadline}s.', file=sys.stderr)
sys.exit(1)
