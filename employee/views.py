import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from employee.services import face as face_svc

logger = logging.getLogger(__name__)


def _int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


@staff_member_required
@require_POST
def api_face_save(request):
    """Register/update an employee's face (called from the admin change page)."""
    try:
        data = json.loads(request.body)
        employee_id = _int(data.get('employee_id'))
        if not employee_id:
            return JsonResponse({'success': False, 'message': 'employee_id required'})
        descriptor = face_svc.parse_descriptor(data.get('descriptor'))
        sample_count = _int(data.get('sample_count')) or 1
        face_svc.save_embedding(
            employee_id=employee_id,
            descriptor=descriptor,
            sample_count=sample_count,
            user_id=request.user.pk,
        )
        return JsonResponse({'success': True, 'message': 'Face registered'})
    except face_svc.FaceError as exc:
        return JsonResponse({'success': False, 'message': str(exc)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Face save failed')
        return JsonResponse({'success': False, 'message': f'Save failed: {exc}'})


@staff_member_required
@require_GET
def api_face_status(request):
    employee_id = _int(request.GET.get('employee_id'))
    if not employee_id:
        return JsonResponse({'success': False, 'message': 'employee_id required'})
    return JsonResponse({'success': True, **face_svc.get_status(employee_id)})


@staff_member_required
@require_POST
def api_face_delete(request):
    try:
        data = json.loads(request.body)
        employee_id = _int(data.get('employee_id'))
        if not employee_id:
            return JsonResponse({'success': False, 'message': 'employee_id required'})
        removed = face_svc.delete_embedding(employee_id, user_id=request.user.pk)
        return JsonResponse({'success': removed,
                             'message': 'Face removed' if removed else 'No face registered'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Face delete failed')
        return JsonResponse({'success': False, 'message': f'Delete failed: {exc}'})
