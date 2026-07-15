"""Apply idempotent schema patches at container start.

init-db.ps1 only runs the full SQL set on a *fresh* database. For an already-
initialized DB, newer additive migrations would be missed. These files are all
guarded (IF NOT EXISTS / COL_LENGTH checks), so applying them on every boot is
safe and keeps a running Docker deploy in sync with the code.

Run:  python deploy/docker/apply_schema_patches.py
"""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen_system.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402

# Additive patches (files 01–22 are the fresh-init baseline). Anything numbered
# at or above this is an idempotent, guarded patch applied on every start.
# Auto-discovered so a NEW patch file never has to be hand-registered here —
# dropping database/NN_*.sql (NN >= threshold) is enough.
PATCH_MIN_NUMBER = 23


def _discover_patches(db_dir):
    """Return additive patch filenames sorted by leading number.

    Matches files like `26_voice_request_logs.sql` with number >= threshold.
    """
    found = []
    for name in os.listdir(db_dir):
        m = re.match(r'^(\d+)[a-z]?_.*\.sql$', name, re.IGNORECASE)
        if m and int(m.group(1)) >= PATCH_MIN_NUMBER:
            found.append((int(m.group(1)), name))
    return [name for _, name in sorted(found)]


def _run_file(path):
    sql = open(path, encoding='utf-8-sig').read()
    # Strip USE [...] — the connection is already bound to the target DB.
    sql = re.sub(r'^\s*USE\s+\[[^\]]+\]\s*;?\s*$', '', sql, flags=re.MULTILINE | re.IGNORECASE)
    batches = [b.strip() for b in re.split(r'^\s*GO\s*$', sql, flags=re.MULTILINE) if b.strip()]
    with connection.cursor() as cur:
        for b in batches:
            cur.execute(b)


def main():
    db_dir = os.path.join(settings.BASE_DIR, 'database')
    patches = _discover_patches(db_dir)
    print(f'  discovered {len(patches)} additive patch(es): {", ".join(patches) or "none"}')
    for name in patches:
        path = os.path.join(db_dir, name)
        if not os.path.exists(path):
            print(f'  skip (missing): {name}')
            continue
        try:
            _run_file(path)
            print(f'  applied: {name}')
        except Exception as exc:  # noqa: BLE001 - never block startup on a patch
            print(f'  WARN {name}: {exc}')


if __name__ == '__main__':
    main()
