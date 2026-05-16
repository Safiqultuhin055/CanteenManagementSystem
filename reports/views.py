import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from pos.models import Order, OrderDetail
from employee.models import Employee
from inventory.models import MenuItem, DailyFoodStock


def _today():
    return timezone.localdate()


@login_required
def reports_hub(request):
    today = _today()
    stats = _summary_stats(today)
    return render(request, 'reports/hub.html', {**stats, 'today': today})


@login_required
def sales_report(request):
    today = _today()
    date_from = request.GET.get('from') or (today - timedelta(days=6)).isoformat()
    date_to = request.GET.get('to') or today.isoformat()

    try:
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        from_date = today - timedelta(days=6)
        to_date = today

    stats = _summary_stats(today)
    trend = _sales_trend(from_date, to_date)
    dept_sales = _department_sales(from_date, to_date)
    top_items = _top_items(from_date, to_date)
    recent_orders = (
        Order.objects.filter(is_deleted=False, order_date__gte=from_date, order_date__lte=to_date)
        .select_related('employee')
        .order_by('-order_time')[:15]
    )

    return render(request, 'reports/sales.html', {
        **stats,
        'today': today,
        'from_date': from_date,
        'to_date': to_date,
        'trend_labels': json.dumps(trend['labels']),
        'trend_values': json.dumps(trend['values']),
        'dept_labels': json.dumps(dept_sales['labels']),
        'dept_values': json.dumps(dept_sales['values']),
        'top_items': top_items,
        'recent_orders': recent_orders,
    })


def _summary_stats(today):
    orders_today = Order.objects.filter(order_date=today, is_deleted=False)
    revenue = orders_today.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
    order_count = orders_today.count()
    credit = orders_today.aggregate(t=Sum('credit_deducted'))['t'] or Decimal('0')

    try:
        low_stock = DailyFoodStock.objects.filter(
            stock_date=today,
            is_deleted=False,
            is_available=True,
        ).annotate(remaining=F('prepared_quantity') - F('sold_quantity')).filter(remaining__lte=5).count()
    except Exception:
        low_stock = MenuItem.objects.filter(is_active=True, is_available=False, is_deleted=False).count()

    return {
        'revenue_today': revenue,
        'orders_today': order_count,
        'credit_today': credit,
        'low_stock': low_stock,
        'employee_count': Employee.objects.filter(is_active=True, is_deleted=False).count(),
    }


def _sales_trend(from_date, to_date):
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


def _department_sales(from_date, to_date):
    rows = (
        Order.objects.filter(
            is_deleted=False,
            order_date__gte=from_date,
            order_date__lte=to_date,
            employee__isnull=False,
        )
        .values('employee__department__department_name')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')[:8]
    )
    labels = [r['employee__department__department_name'] or 'Unknown' for r in rows]
    values = [float(r['total'] or 0) for r in rows]
    if not labels:
        labels, values = ['No data'], [0]
    return {'labels': labels, 'values': values}


def _top_items(from_date, to_date):
    rows = (
        OrderDetail.objects.filter(
            is_deleted=False,
            order__order_date__gte=from_date,
            order__order_date__lte=to_date,
            order__is_deleted=False,
        )
        .values('item_name')
        .annotate(
            qty=Sum('quantity'),
            revenue=Sum('total_price'),
        )
        .order_by('-qty')[:10]
    )
    return list(rows)
