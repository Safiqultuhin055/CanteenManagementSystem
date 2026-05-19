import json
import logging
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.business_date import get_business_date
from kitchen.realtime import current_version, notify_kitchen_queue_changed, wait_for_change
from pos.models import Order, OrderDetail

logger = logging.getLogger(__name__)


def _order_items(order_id):
    return list(
        OrderDetail.objects.filter(order_id=order_id, is_deleted=False).values(
            'item_name', 'quantity', 'total_price'
        )
    )


def _serialize_kitchen_entry(queue_row=None, order=None):
    """Build API payload from KitchenQueue row or Order fallback."""
    if queue_row:
        order = queue_row.order
        return {
            'id': queue_row.id,
            'order_id': order.id,
            'order_number': order.order_number,
            'token_number': queue_row.token_number,
            'status': queue_row.queue_status,
            'priority': queue_row.priority or 0,
            'customer': _customer_name(order),
            'items': _order_items(order.id),
            'total_amount': float(order.total_amount),
            'order_time': order.order_time.isoformat() if order.order_time else None,
            'wait_minutes': _wait_minutes(queue_row.created_at or order.order_time),
        }

    status = order.kitchen_status or 'PENDING'
    if status in ('PREPARING', 'IN_PROGRESS'):
        status = 'PENDING'
    return {
        'id': None,
        'order_id': order.id,
        'order_number': order.order_number,
        'token_number': order.token_number,
        'status': status,
        'priority': 0,
        'customer': _customer_name(order),
        'items': _order_items(order.id),
        'total_amount': float(order.total_amount),
        'order_time': order.order_time.isoformat() if order.order_time else None,
        'wait_minutes': _wait_minutes(order.order_time),
        'from_order_only': True,
    }


def _customer_name(order):
    if order.employee_id and order.employee:
        return order.employee.full_name
    return order.customer_name or 'Guest'


def _wait_minutes(dt):
    if not dt:
        return 0
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    delta = timezone.now() - dt
    return max(0, int(delta.total_seconds() // 60))


@login_required
def kds_dashboard(request):
    today = get_business_date()
    from kitchen.models import KitchenQueue

    pending = KitchenQueue.objects.filter(
        queue_date=today,
        queue_status__in=['PENDING', 'IN_PROGRESS'],
        is_active=True,
    ).count()

    return render(request, 'kitchen/kds.html', {
        'stats': {'pending': pending, 'today': today},
    })


@login_required
def api_get_queue(request):
    from kitchen.models import KitchenQueue

    today = get_business_date()
    data = []
    seen_orders = set()

    queues = (
        KitchenQueue.objects.filter(
            queue_date=today,
            queue_status__in=['PENDING', 'IN_PROGRESS'],
            is_active=True,
        )
        .select_related('order', 'order__employee')
        .order_by('-priority', 'created_at', 'id')
    )

    for q in queues:
        if q.order and not q.order.is_deleted:
            entry = _serialize_kitchen_entry(queue_row=q)
            if entry['status'] == 'IN_PROGRESS':
                entry['status'] = 'PENDING'
            data.append(entry)
            seen_orders.add(q.order_id)

    if not data:
        orders = (
            Order.objects.filter(
                order_date=today,
                is_deleted=False,
                kitchen_status__in=['PENDING', 'PREPARING', 'IN_PROGRESS'],
            )
            .select_related('employee')
            .order_by('-order_time')[:50]
        )
        for order in orders:
            if order.id not in seen_orders:
                data.append(_serialize_kitchen_entry(order=order))

    from distribution.models import DistributionQueue
    from distribution.services import sync_ready_pickup_queue

    sync_ready_pickup_queue(today)

    ready_today = list(
        DistributionQueue.objects.filter(
            queue_date=today,
            queue_status__in=['PENDING', 'READY_FOR_PICKUP'],
            is_active=True,
        )
        .select_related('order', 'order__employee')
        .order_by('-updated_at', '-id')[:12]
    )
    ready_cards = []
    for dq in ready_today:
        if dq.order and not dq.order.is_deleted:
            ready_cards.append({
                'token_number': dq.token_number,
                'customer': _customer_name(dq.order),
                'order_number': dq.order.order_number,
            })

    return JsonResponse({
        'success': True,
        'version': current_version(),
        'orders': data,
        'ready_pickup': ready_cards,
        'counts': {
            'pending': len(data),
            'ready': len(ready_cards),
        },
    })


@login_required
@require_GET
def api_kitchen_stream(request):
    """SSE: push when POS sale or kitchen status changes (no polling)."""
    try:
        since = int(request.GET.get('since', 0))
    except (TypeError, ValueError):
        since = 0

    def event_stream():
        client_since = since
        while True:
            new_version = wait_for_change(client_since, timeout=25.0)
            if new_version > client_since:
                payload = json.dumps({'version': new_version})
                yield f'event: update\ndata: {payload}\n\n'
                client_since = new_version
            else:
                yield ': heartbeat\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
@require_POST
def api_update_status(request):
    try:
        body = json.loads(request.body)
        queue_id = body.get('queue_id')
        order_id = body.get('order_id')
        new_status = body.get('status')
        user_id = request.user.pk

        if new_status not in ('READY',):
            return JsonResponse({'success': False, 'message': 'Invalid status'})

        if queue_id:
            return _update_via_sp(queue_id, new_status, user_id)

        if order_id:
            return _update_via_order(order_id, new_status, user_id)

        return JsonResponse({'success': False, 'message': 'Missing queue or order id'})
    except Exception as exc:
        logger.exception('Kitchen status update failed')
        return JsonResponse({'success': False, 'message': str(exc)})


def _update_via_sp(queue_id, new_status, user_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                EXEC dbo.usp_UpdateKitchenStatus
                    @QueueId = %s,
                    @NewStatus = %s,
                    @UpdatedBy = %s,
                    @Remarks = NULL
                """,
                [queue_id, new_status, user_id],
            )
            row = cursor.fetchone()
        if row and row[0]:
            notify_kitchen_queue_changed()
            return JsonResponse({'success': True, 'message': row[1] if len(row) > 1 else 'Updated'})
        return JsonResponse({'success': False, 'message': row[1] if row else 'Update failed'})
    except Exception:
        return _update_via_orm_queue(queue_id, new_status, user_id)


def _update_via_orm_queue(queue_id, new_status, user_id):
    from kitchen.models import KitchenQueue
    from distribution.models import DistributionQueue

    q = KitchenQueue.objects.select_related('order').get(pk=queue_id)
    old = q.queue_status
    q.queue_status = new_status
    if new_status == 'IN_PROGRESS' and not q.started_at:
        q.started_at = timezone.now()
    if new_status == 'READY':
        q.completed_at = timezone.now()
    q.save(update_fields=['queue_status', 'started_at', 'completed_at', 'updated_at'])

    order = q.order
    order.kitchen_status = new_status
    if new_status == 'READY':
        order.order_status = 'READY'
        order.distribution_status = 'READY_FOR_PICKUP'
    order.save(update_fields=['kitchen_status', 'order_status', 'distribution_status', 'updated_at'])

    pickup_msg = f'{old} → {new_status}'
    if new_status == 'READY':
        dq, created = DistributionQueue.objects.get_or_create(
            order=order,
            defaults={
                'token_number': q.token_number,
                'queue_date': q.queue_date or get_business_date(),
                'queue_status': 'READY_FOR_PICKUP',
            },
        )
        if not created:
            dq.queue_status = 'READY_FOR_PICKUP'
            dq.token_number = q.token_number
            dq.save(update_fields=['queue_status', 'token_number', 'updated_at'])
        pickup_msg = (
            f'Token #{q.token_number} is ready for pickup — '
            f'check Distribution counter'
        )
        from distribution.services import sync_ready_pickup_queue
        sync_ready_pickup_queue(q.queue_date or get_business_date())

    notify_kitchen_queue_changed()
    return JsonResponse({
        'success': True,
        'message': pickup_msg,
        'token_number': q.token_number,
        'ready_for_pickup': new_status == 'READY',
    })


def _update_via_order(order_id, new_status, user_id):
    from kitchen.models import KitchenQueue
    from distribution.models import DistributionQueue

    order = Order.objects.get(pk=order_id, is_deleted=False)
    kq, created = KitchenQueue.objects.get_or_create(
        order=order,
        defaults={
            'token_number': order.token_number,
            'queue_status': 'PENDING',
            'queue_date': order.order_date or get_business_date(),
        },
    )
    return _update_via_orm_queue(kq.id, new_status, user_id)
