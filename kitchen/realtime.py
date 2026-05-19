"""In-process kitchen queue change notifications (SSE for KDS)."""
import threading
import time

_lock = threading.Lock()
_version = 0


def current_version() -> int:
    with _lock:
        return _version


def notify_kitchen_queue_changed() -> int:
    global _version
    with _lock:
        _version += 1
        return _version


def wait_for_change(since: int, timeout: float = 25.0) -> int:
    """Block until queue version increases or timeout (for SSE long-poll)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with _lock:
            if _version > since:
                return _version
        time.sleep(0.25)
    with _lock:
        return _version
