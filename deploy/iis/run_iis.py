"""
WSGI entry for IIS HttpPlatformHandler.
IIS sets HTTP_PLATFORM_PORT; Waitress listens on 127.0.0.1 only (IIS is the public front door).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen_system.settings')

port = int(os.environ.get('HTTP_PLATFORM_PORT', '8000'))
log_dir = ROOT / 'logs'
log_dir.mkdir(exist_ok=True)
boot_log = log_dir / 'iis_boot.log'


def _log(msg: str) -> None:
    with boot_log.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


try:
    from django.core.wsgi import get_wsgi_application
    from waitress import serve

    _log(f'Starting Waitress on 127.0.0.1:{port} FORCE_SCRIPT_NAME={os.environ.get("FORCE_SCRIPT_NAME", "")}')
    serve(get_wsgi_application(), host='127.0.0.1', port=port, threads=8)
except Exception as exc:
    _log(f'BOOT FAILED: {exc!r}')
    raise
