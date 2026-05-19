"""Dashboard metrics aligned with SQL Server business date."""
import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate

from core.business_date import get_business_date

logger = logging.getLogger(__name__)


def get_dashboard_data():
    today = get_business_date()
    week_start = today - timedelta(days=6)

    stats = _empty_stats()
    recent_orders = []
    dept_breakdown = []
    top_items = []
    trend_labels = json.dumps([])
    trend_values = json.dumps([])

    try:
        stats = _fetch_stats(today, week_start)
        recent_orders = _fetch_recent_orders(today)
        dept_breakdown = _fetch_department_breakdown()
        top_items = _fetch_top_items(today, limit=6)
        trend = _sales_trend(week_start, today)
        trend_labels = json.dumps(trend['labels'])
        trend_values = json.dumps(trend['values'])
    except Exception as exc:
        logger.exception('Dashboard data fetch failed: %s', exc)
        stats['fetch_error'] = str(exc)

    return {
        **stats,
        'today': today,
        'recent_orders': recent_orders,
        'dept_breakdown': dept_breakdown,
        'top_items': top_items,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
    }


def _empty_stats():
    return {
        'employee_count': 0,
        'active_employee_count': 0,
        'menu_item_count': 0,
        'department_count': 0,
        'card_count': 0,
        'order_count_today': 0,
        'sales_today': Decimal('0'),
        'sales_yesterday': Decimal('0'),
        'orders_yesterday': 0,
        'sales_change_pct': None,
        'orders_change_pct': None,
        'week_sales': Decimal('0'),
        'week_orders': 0,
        'credit_today': Decimal('0'),
        'advance_today': Decimal('0'),
        'kitchen_pending': 0,
        'kitchen_preparing': 0,
        'kitchen_ready': 0,
        'ready_pickup': 0,
        'completed_today': 0,
        'distribution_pending': 0,
        'low_stock': 0,
        'guest_orders_today': 0,
        'total_advance_balance': Decimal('0'),
        'total_spent_all': Decimal('0'),
        'fetch_error': None,
    }


def _fetch_stats(today, week_start):
    from employee.models import Employee, EmployeeCard, Department
    from inventory.models import MenuItem, DailyFoodStock
    from pos.models import Order
    from balance.models import EmployeeBalance

    emp_qs = Employee.objects.filter(is_deleted=False)
    order_today = Order.objects.filter(order_date=today, is_deleted=False)
    order_yesterday = Order.objects.filter(
        order_date=today - timedelta(days=1), is_deleted=False,
    )
    order_week = Order.objects.filter(
        order_date__gte=week_start, order_date__lte=today, is_deleted=False,
    )

    sales_today = order_today.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
    sales_yesterday = order_yesterday.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
    orders_today = order_today.count()
    orders_yesterday = order_yesterday.count()

    bal = EmployeeBalance.objects.aggregate(
        advance=Sum('advance_balance'),
        spent=Sum('total_spent'),
    )
    credits = order_today.aggregate(
        credit=Sum('credit_deducted'),
        advance=Sum('advance_deducted'),
    )

    low_stock = _low_stock_count(today)

    return {
        'employee_count': emp_qs.count(),
        'active_employee_count': emp_qs.filter(is_active=True).count(),
        'menu_item_count': MenuItem.objects.filter(is_deleted=False, is_active=True).count(),
        'department_count': Department.objects.filter(is_deleted=False).count(),
        'card_count': EmployeeCard.objects.filter(is_deleted=False, card_status='ACTIVE').count(),
        'order_count_today': orders_today,
        'sales_today': sales_today,
        'sales_yesterday': sales_yesterday,
        'orders_yesterday': orders_yesterday,
        'sales_change_pct': _pct_change(sales_today, sales_yesterday),
        'orders_change_pct': _pct_change(orders_today, orders_yesterday),
        'week_sales': order_week.aggregate(t=Sum('total_amount'))['t'] or Decimal('0'),
        'week_orders': order_week.count(),
        'credit_today': credits['credit'] or Decimal('0'),
        'advance_today': credits['advance'] or Decimal('0'),
        'kitchen_pending': order_today.filter(kitchen_status='PENDING').count(),
        'kitchen_preparing': order_today.filter(
            kitchen_status__in=('PREPARING', 'IN_PROGRESS'),
        ).count(),
        'kitchen_ready': order_today.filter(kitchen_status='READY').count(),
        'ready_pickup': order_today.filter(
            distribution_status='READY_FOR_PICKUP',
        ).count(),
        'completed_today': order_today.filter(
            distribution_status='PICKED_UP',
        ).count(),
        'distribution_pending': order_today.filter(distribution_status='PENDING').count(),
        'low_stock': low_stock,
        'guest_orders_today': order_today.filter(employee__isnull=True).count(),
        'total_advance_balance': bal['advance'] or Decimal('0'),
        'total_spent_all': bal['spent'] or Decimal('0'),
        'fetch_error': None,
    }


def _pct_change(current, previous):
    if not previous:
        return None
    try:
        return round((float(current) - float(previous)) / float(previous) * 100, 1)
    except (TypeError, ZeroDivisionError):
        return None


def _low_stock_count(today):
    from inventory.models import MenuItem, DailyFoodStock

    try:
        return DailyFoodStock.objects.filter(
            stock_date=today,
            is_deleted=False,
            is_available=True,
        ).annotate(
            remaining=F('prepared_quantity') - F('sold_quantity') - F('waste_quantity'),
        ).filter(remaining__lte=5).count()
    except Exception:
        return MenuItem.objects.filter(
            is_active=True, is_available=False, is_deleted=False,
        ).count()


def _sales_trend(from_date, to_date):
    from pos.models import Order

    rows = (
        Order.objects.filter(
            is_deleted=False,
            order_date__gte=from_date,
            order_date__lte=to_date,
        )
        .annotate(day=TruncDate('order_date'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('day')
    )
    by_day = {r['day']: float(r['total'] or 0) for r in rows}
    labels, values = [], []
    d = from_date
    while d <= to_date:
        labels.append(d.strftime('%a %d'))
        values.append(by_day.get(d, 0))
        d += timedelta(days=1)
    return {'labels': labels, 'values': values}


def _fetch_recent_orders(today, limit=10):
    from pos.models import Order

    try:
        return list(
            Order.objects.filter(is_deleted=False, order_date=today)
            .select_related('employee')
            .order_by('-order_time')[:limit]
        )
    except Exception as exc:
        logger.warning('Recent orders: %s', exc)
        return []


def _fetch_department_breakdown(limit=6):
    from employee.models import Employee

    try:
        rows = (
            Employee.objects.filter(is_deleted=False, is_active=True)
            .values('department__department_name')
            .annotate(cnt=Count('id'))
            .order_by('-cnt')[:limit]
        )
        return [
            {'name': r['department__department_name'] or 'Unknown', 'count': r['cnt']}
            for r in rows
        ]
    except Exception as exc:
        logger.warning('Department breakdown: %s', exc)
        return []


def _fetch_top_items(today, limit=6):
    from pos.models import OrderDetail

    try:
        return list(
            OrderDetail.objects.filter(
                is_deleted=False,
                order__order_date=today,
                order__is_deleted=False,
            )
            .values('item_name')
            .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
            .order_by('-qty')[:limit]
        )
    except Exception as exc:
        logger.warning('Top items: %s', exc)
        return []
