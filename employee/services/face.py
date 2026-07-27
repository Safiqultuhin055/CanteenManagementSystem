"""Face embedding storage and matching.

Descriptors are 128-d float vectors produced client-side by face-api.js.
We store one (averaged) descriptor per employee and match live descriptors
against them with plain euclidean distance — no numpy needed for 128 floats.
"""
import json
import math
from datetime import datetime

from employee.models import Employee, FaceEmbedding

DESCRIPTOR_LEN = 128
# Stricter than face-api's 0.6 default — this gates POS login, so a false accept
# means charging the wrong employee. Distance below this = same person.
DEFAULT_THRESHOLD = 0.48
# The best match must beat the 2nd-best (a different employee) by at least this
# much, otherwise the result is ambiguous and rejected.
MATCH_MARGIN = 0.06


class FaceError(Exception):
    """Bad descriptor payload."""


def parse_descriptor(raw) -> list[float]:
    """Validate an incoming descriptor into a list of 128 floats."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise FaceError('Invalid descriptor JSON') from exc
    if not isinstance(raw, (list, tuple)) or len(raw) != DESCRIPTOR_LEN:
        raise FaceError(f'Descriptor must be {DESCRIPTOR_LEN} numbers')
    try:
        vec = [float(x) for x in raw]
    except (ValueError, TypeError) as exc:
        raise FaceError('Descriptor must be numeric') from exc
    if not any(vec):
        raise FaceError('Empty descriptor')
    return vec


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) * (x - y) for x, y in zip(a, b)))


def save_embedding(*, employee_id: int, descriptor: list[float],
                   sample_count: int = 1, user_id=None) -> FaceEmbedding:
    """Create or overwrite the employee's registered face."""
    emp = Employee.objects.filter(id=employee_id, is_deleted=False).first()
    if not emp:
        raise FaceError('Employee not found')

    payload = json.dumps(descriptor)
    row = FaceEmbedding.objects.filter(employee_id=employee_id).first()
    if row:
        row.embedding = payload
        row.sample_count = sample_count
        row.model = 'face-api-128'
        row.is_active = True
        row.is_deleted = False
        row.updated_by = user_id
        row.updated_at = datetime.now()
        row.save()
    else:
        row = FaceEmbedding.objects.create(
            employee_id=employee_id,
            embedding=payload,
            sample_count=sample_count,
            model='face-api-128',
            is_active=True,
            is_deleted=False,
            created_by=user_id,
        )
    return row


def get_status(employee_id: int) -> dict:
    row = FaceEmbedding.objects.filter(
        employee_id=employee_id, is_active=True, is_deleted=False,
    ).first()
    if not row:
        return {'registered': False}
    return {
        'registered': True,
        'sample_count': row.sample_count,
        'updated_at': (row.updated_at or row.created_at).isoformat() if (row.updated_at or row.created_at) else None,
    }


def delete_embedding(employee_id: int, user_id=None) -> bool:
    row = FaceEmbedding.objects.filter(employee_id=employee_id, is_deleted=False).first()
    if not row:
        return False
    row.is_active = False
    row.is_deleted = True
    row.updated_by = user_id
    row.updated_at = datetime.now()
    row.save()
    return True


def find_match(descriptor: list[float], threshold: float = DEFAULT_THRESHOLD,
               margin: float = MATCH_MARGIN):
    """Return (employee, distance) for the closest registered face, but only if
    the match is confident: under `threshold` AND clearly ahead of the next
    closest employee by `margin`. Otherwise (None, best_distance)."""
    rows = (
        FaceEmbedding.objects.filter(is_active=True, is_deleted=False)
        .select_related('employee')
    )
    best_emp = None
    best_dist = float('inf')
    second_dist = float('inf')  # closest distance to a DIFFERENT employee
    for row in rows:
        emp = row.employee
        if not emp or not emp.is_active or emp.is_deleted:
            continue
        try:
            stored = json.loads(row.embedding)
        except (ValueError, TypeError):
            continue
        if len(stored) != DESCRIPTOR_LEN:
            continue
        dist = euclidean(descriptor, stored)
        if dist < best_dist:
            if best_emp is not None and emp.id != best_emp.id:
                second_dist = best_dist
            best_dist = dist
            best_emp = emp
        elif dist < second_dist and (best_emp is None or emp.id != best_emp.id):
            second_dist = dist

    if best_emp is None or best_dist > threshold:
        return None, best_dist
    # Ambiguous — another registered face is nearly as close → refuse.
    if second_dist - best_dist < margin:
        return None, best_dist
    return best_emp, best_dist
