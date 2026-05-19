"""Distribution / ready-for-pickup queue helpers."""

import logging

from django.utils import timezone

from core.business_date import get_business_date
from pos.models import Order, OrderDetail

logger = logging.getLogger(__name__)


def _order_items(order_id):
    return list(
        OrderDetail.objects.filter(order_id=order_id, is_deleted=False).values(
            'item_name', 'quantity'
        )
    )


def sync_ready_pickup_queue(queue_date=None):
    """
    Ensure every kitchen-READY order has a distribution_queue row for pickup.
    Upgrades legacy PENDING rows to READY_FOR_PICKUP.
    """
    from distribution.models import DistributionQueue

    queue_date = queue_date or get_business_date()
    now = timezone.now()

    upgraded = DistributionQueue.objects.filter(
        queue_date=queue_date,
        queue_status='PENDING',
        is_active=True,
        order__kitchen_status='READY',
        order__is_deleted=False,
    ).update(queue_status='READY_FOR_PICKUP', updated_at=now)

    existing_order_ids = set(
        DistributionQueue.objects.filter(queue_date=queue_date).values_list('order_id', flat=True)
    )

    ready_orders = Order.objects.filter(
        order_date=queue_date,
        is_deleted=False,
        kitchen_status='READY',
    ).exclude(id__in=existing_order_ids)

    created = 0
    for order in ready_orders:
        DistributionQueue.objects.create(
            order=order,
            token_number=order.token_number,
            queue_date=queue_date,
            queue_status='READY_FOR_PICKUP',
        )
        if order.distribution_status != 'READY_FOR_PICKUP':
            order.distribution_status = 'READY_FOR_PICKUP'
            order.save(update_fields=['distribution_status', 'updated_at'])
        created += 1

    return {'created': created, 'upgraded': upgraded}


def get_distribution_board(queue_date=None):
    """Return preparing + ready-for-pickup data for counter API."""
    from distribution.models import DistributionQueue
    from kitchen.models import KitchenQueue

    queue_date = queue_date or get_business_date()
    sync_ready_pickup_queue(queue_date)

    preparing = list(
        KitchenQueue.objects.filter(
            queue_date=queue_date,
            queue_status__in=['PENDING', 'IN_PROGRESS'],
            is_active=True,
        )
        .order_by('token_number')
        .values_list('token_number', flat=True)
    )

    ready_qs = (
        DistributionQueue.objects.filter(
            queue_date=queue_date,
            queue_status__in=['PENDING', 'READY_FOR_PICKUP'],
            is_active=True,
        )
        .select_related('order', 'order__employee')
        .order_by('token_number')
    )

    ready_details = []
    for dq in ready_qs:
        order = dq.order
        items = _order_items(order.id) if order else []
        ready_details.append({
            'token': dq.token_number,
            'queue_id': dq.id,
            'status': dq.queue_status,
            'called': bool(dq.called_at),
            'called_at': dq.called_at.isoformat() if dq.called_at else None,
            'customer': (
                order.employee.full_name if order and order.employee
                else (order.customer_name if order else 'Guest')
            ),
            'order_number': order.order_number if order else '',
            'items': items,
            'item_summary': ', '.join(f"{i['quantity']}x {i['item_name']}" for i in items[:3]),
        })

    now_serving = sorted(
        [r for r in ready_details if r['called']],
        key=lambda r: r['called_at'] or '',
        reverse=True,
    )

    picked_today = DistributionQueue.objects.filter(
        queue_date=queue_date, queue_status='PICKED_UP', is_active=True
    ).count()

    return {
        'preparing': preparing,
        'ready': [r['token'] for r in ready_details],
        'ready_details': ready_details,
        'now_serving': now_serving,
        'picked_today': picked_today,
        'queue_date': queue_date.isoformat(),
    }
