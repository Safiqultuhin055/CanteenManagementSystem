"""Report query helpers."""
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Sum

from inventory.models import DailyFoodStock, MenuItem
from pos.models import Order, OrderDetail


def parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return default


def parse_month(value: str | None, default: date) -> tuple[int, int]:
    """Return (year, month) from YYYY-MM or default."""
    if value:
        try:
            if len(value) == 7:
                dt = datetime.strptime(value + '-01', '%Y-%m-%d')
                return dt.year, dt.month
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.year, dt.month
        except ValueError:
            pass
    return default.year, default.month


def orders_in_range(from_date: date, to_date: date):
    return Order.objects.filter(
        is_deleted=False,
        order_date__gte=from_date,
        order_date__lte=to_date,
    )


def daily_sales_report(report_date: date):
    qs = orders_in_range(report_date, report_date)
    agg = qs.aggregate(
        revenue=Sum('total_amount'),
        orders=Count('id'),
        credit=Sum('credit_deducted'),
        advance=Sum('advance_deducted'),
    )
    revenue = agg['revenue'] or Decimal('0')
    order_count = agg['orders'] or 0

    item_rows = (
        OrderDetail.objects.filter(
            is_deleted=False,
            order__order_date=report_date,
            order__is_deleted=False,
        )
        .values('item_name')
        .annotate(
            qty=Sum('quantity'),
            revenue=Sum('total_price'),
        )
        .order_by('-qty')
    )

    orders = (
        qs.select_related('employee', 'created_by')
        .order_by('-order_time')
    )

    items_sold = sum(r['qty'] or 0 for r in item_rows)

    return {
        'report_date': report_date,
        'revenue': revenue,
        'order_count': order_count,
        'items_sold': items_sold,
        'credit': agg['credit'] or Decimal('0'),
        'advance': agg['advance'] or Decimal('0'),
        'avg_order': (revenue / order_count) if order_count else Decimal('0'),
        'item_rows': list(item_rows),
        'orders': orders,
    }


def user_wise_sales_report(from_date: date, to_date: date):
    rows = (
        orders_in_range(from_date, to_date)
        .values('created_by_id', 'created_by__full_name', 'created_by__username')
        .annotate(
            orders=Count('id'),
            revenue=Sum('total_amount'),
            credit=Sum('credit_deducted'),
        )
        .order_by('-revenue')
    )
    result = []
    for row in rows:
        name = row['created_by__full_name'] or row['created_by__username']
        if not name:
            name = 'Unassigned / System'
        result.append({
            'user_id': row['created_by_id'],
            'user_name': name,
            'orders': row['orders'] or 0,
            'revenue': row['revenue'] or Decimal('0'),
            'credit': row['credit'] or Decimal('0'),
        })

    totals = orders_in_range(from_date, to_date).aggregate(
        orders=Count('id'),
        revenue=Sum('total_amount'),
    )
    return {
        'from_date': from_date,
        'to_date': to_date,
        'rows': result,
        'total_orders': totals['orders'] or 0,
        'total_revenue': totals['revenue'] or Decimal('0'),
    }


def monthly_summary_report(year: int, month: int):
    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])

    day_map = {
        r['order_date']: r
        for r in orders_in_range(first, last)
        .values('order_date')
        .annotate(
            orders=Count('id'),
            revenue=Sum('total_amount'),
        )
    }

    days = []
    d = first
    while d <= last:
        row = day_map.get(d, {})
        days.append({
            'date': d,
            'orders': row.get('orders') or 0,
            'revenue': row.get('revenue') or Decimal('0'),
        })
        d += timedelta(days=1)

    month_totals = orders_in_range(first, last).aggregate(
        orders=Count('id'),
        revenue=Sum('total_amount'),
        credit=Sum('credit_deducted'),
    )

    top_items = (
        OrderDetail.objects.filter(
            is_deleted=False,
            order__order_date__gte=first,
            order__order_date__lte=last,
            order__is_deleted=False,
        )
        .values('item_name')
        .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
        .order_by('-qty')[:10]
    )

    return {
        'year': year,
        'month': month,
        'month_label': first.strftime('%B %Y'),
        'from_date': first,
        'to_date': last,
        'days': days,
        'total_orders': month_totals['orders'] or 0,
        'total_revenue': month_totals['revenue'] or Decimal('0'),
        'total_credit': month_totals['credit'] or Decimal('0'),
        'top_items': list(top_items),
    }


def inventory_status_report(stock_date: date):
    stocks = (
        DailyFoodStock.objects.filter(
            stock_date=stock_date,
            is_deleted=False,
        )
        .select_related('menu_item', 'menu_item__category')
        .order_by('menu_item__category__category_name', 'menu_item__item_name')
    )

    rows = []
    low_count = out_count = 0
    for stock in stocks:
        prepared = int(stock.prepared_quantity or 0)
        sold = int(stock.sold_quantity or 0)
        waste = int(stock.waste_quantity or 0)
        remaining = max(0, prepared - sold - waste)
        if not stock.is_available or remaining <= 0:
            status = 'out'
            out_count += 1
        elif remaining <= 5:
            status = 'low'
            low_count += 1
        else:
            status = 'ok'
        rows.append({
            'item_name': stock.menu_item.item_name,
            'item_code': stock.menu_item.item_code,
            'category': stock.menu_item.category.category_name,
            'prepared': prepared,
            'sold': sold,
            'waste': waste,
            'remaining': remaining,
            'unit_price': stock.unit_price,
            'is_available': stock.is_available,
            'status': status,
        })

    menu_without_stock = MenuItem.objects.filter(
        is_active=True,
        is_deleted=False,
    ).exclude(
        id__in=[s.menu_item_id for s in stocks],
    ).select_related('category').order_by('category__category_name', 'item_name')

    return {
        'stock_date': stock_date,
        'rows': rows,
        'missing_items': list(menu_without_stock),
        'low_count': low_count,
        'out_count': out_count,
        'item_count': len(rows),
    }
