import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.business_date import get_business_date
from .services import get_distribution_board, sync_ready_pickup_queue

logger = logging.getLogger(__name__)


@login_required
def distribution_dashboard(request):
    today = get_business_date()
    sync_ready_pickup_queue(today)
    board = get_distribution_board(today)

    from distribution.models import DistributionQueue

    ready = len(board['ready_details'])
    preparing = len(board['preparing'])

    return render(request, 'distribution/counter.html', {
        'stats': {
            'ready': ready,
            'preparing': preparing,
            'picked': board['picked_today'],
            'today': today,
        },
    })


def token_display(request):
    return render(request, 'distribution/token_display.html')


def api_get_tokens(request):
    board = get_distribution_board()
    return JsonResponse({
        'success': True,
        **board,
    })


@login_required
@require_POST
def api_call_token(request):
    """Announce token on display (ready for customer pickup)."""
    from distribution.models import DistributionQueue

    try:
        body = json.loads(request.body)
        token_number = int(body.get('token_number'))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid token number'})

    today = get_business_date()
    sync_ready_pickup_queue(today)

    q = DistributionQueue.objects.filter(
        token_number=token_number,
        queue_date=today,
        queue_status__in=['PENDING', 'READY_FOR_PICKUP'],
        is_active=True,
    ).select_related('order').first()

    if not q:
        return JsonResponse({'success': False, 'message': 'Token not in ready queue'})

    q.queue_status = 'READY_FOR_PICKUP'
    q.called_at = timezone.now()
    q.save(update_fields=['queue_status', 'called_at', 'updated_at'])

    if q.order and q.order.distribution_status != 'READY_FOR_PICKUP':
        q.order.distribution_status = 'READY_FOR_PICKUP'
        q.order.save(update_fields=['distribution_status', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': f'Token #{token_number} called — ready for pickup',
    })


@login_required
@require_POST
def api_mark_delivered(request):
    try:
        body = json.loads(request.body)
        token_number = body.get('token_number')
        user_id = request.user.pk

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    EXEC dbo.usp_CompleteDistribution
                        @TokenNumber = %s,
                        @HandledBy = %s,
                        @CardVerified = 1,
                        @Remarks = NULL
                    """,
                    [token_number, user_id],
                )
                row = cursor.fetchone()
            if row and row[0]:
                return JsonResponse({'success': True, 'message': 'Order delivered'})
        except Exception:
            logger.debug('usp_CompleteDistribution unavailable, using ORM')

        return _deliver_via_orm(token_number, user_id)
    except Exception as exc:
        logger.exception('Distribution deliver failed')
        return JsonResponse({'success': False, 'message': str(exc)})


def _deliver_via_orm(token_number, user_id):
    from distribution.models import DistributionQueue

    today = get_business_date()
    q = DistributionQueue.objects.filter(
        token_number=token_number,
        queue_date=today,
        queue_status__in=['PENDING', 'READY_FOR_PICKUP'],
        is_active=True,
    ).select_related('order').first()

    if not q:
        return JsonResponse({'success': False, 'message': 'Token not found or already picked up'})

    q.queue_status = 'PICKED_UP'
    q.picked_up_at = timezone.now()
    q.handled_by_id = user_id
    q.save(update_fields=['queue_status', 'picked_up_at', 'handled_by_id', 'updated_at'])

    if q.order:
        q.order.distribution_status = 'PICKED_UP'
        q.order.order_status = 'DELIVERED'
        q.order.save(update_fields=['distribution_status', 'order_status', 'updated_at'])

    return JsonResponse({'success': True, 'message': f'Token #{token_number} delivered'})
