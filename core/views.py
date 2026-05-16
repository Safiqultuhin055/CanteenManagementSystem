from decimal import Decimal
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from users.permissions import is_admin_user, user_has_permission

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    db_error = None
    try:
        connection.ensure_connection()
    except Exception as exc:
        db_error = str(exc)
        logger.exception('Dashboard database connection failed')

    ctx = _build_dashboard_context(today, db_error)
    return render(request, 'core/dashboard.html', ctx)


def _build_dashboard_context(today, db_error):
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = 'Good morning'
    elif hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'

    stats = {
        'employee_count': 0,
        'menu_item_count': 0,
        'department_count': 0,
        'card_count': 0,
        'order_count_today': 0,
        'sales_today': Decimal('0'),
        'kitchen_pending': 0,
        'distribution_pending': 0,
        'total_advance_balance': Decimal('0'),
        'total_spent_all': Decimal('0'),
        'active_employee_count': 0,
    }
    recent_orders = []
    dept_breakdown = []

    if not db_error:
        stats = _fetch_dashboard_stats(today)
        recent_orders = _fetch_recent_orders(today)
        dept_breakdown = _fetch_department_breakdown()

    stats_empty = (
        not db_error
        and stats['employee_count'] == 0
        and stats['menu_item_count'] == 0
        and stats['order_count_today'] == 0
    )

    return {
        **stats,
        'greeting': greeting,
        'today': today,
        'db_error': db_error,
        'stats_empty': stats_empty,
        'debug': settings.DEBUG,
        'recent_orders': recent_orders,
        'dept_breakdown': dept_breakdown,
    }


def _fetch_dashboard_stats(today):
    from employee.models import Employee, EmployeeCard, Department
    from inventory.models import MenuItem
    from pos.models import Order
    from balance.models import EmployeeBalance

    emp_qs = Employee.objects.filter(is_deleted=False)
    order_qs = Order.objects.filter(order_date=today, is_deleted=False)
    sales = order_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    bal = EmployeeBalance.objects.aggregate(
        advance=Sum('advance_balance'),
        spent=Sum('total_spent'),
    )

    return {
        'employee_count': emp_qs.count(),
        'active_employee_count': emp_qs.filter(is_active=True).count(),
        'menu_item_count': MenuItem.objects.filter(is_deleted=False, is_active=True).count(),
        'department_count': Department.objects.filter(is_deleted=False).count(),
        'card_count': EmployeeCard.objects.filter(is_deleted=False, card_status='ACTIVE').count(),
        'order_count_today': order_qs.count(),
        'sales_today': sales,
        'kitchen_pending': order_qs.filter(kitchen_status__in=('PENDING', 'PREPARING')).count(),
        'distribution_pending': order_qs.filter(distribution_status='PENDING').count(),
        'total_advance_balance': bal['advance'] or Decimal('0'),
        'total_spent_all': bal['spent'] or Decimal('0'),
    }


def _fetch_recent_orders(today, limit=8):
    try:
        from pos.models import Order
        return list(
            Order.objects.filter(is_deleted=False)
            .select_related('employee')
            .order_by('-order_time')[:limit]
        )
    except Exception as exc:
        logger.warning('Recent orders fetch failed: %s', exc)
        return []


def _fetch_department_breakdown(limit=5):
    try:
        from employee.models import Employee
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
        logger.warning('Department breakdown failed: %s', exc)
        return []


@login_required
def help_user_manual(request):
    return render(request, 'core/help_document.html', {
        'doc_title': 'User Manual',
        'doc_subtitle': 'How to use CanteenSys day to day',
        'doc_type': 'user',
        'doc_icon': 'bi-book',
        'doc_color': 'primary',
    })


@login_required
def help_technical(request):
    allowed = (
        request.user.is_superuser
        or is_admin_user(request.user)
        or user_has_permission(request.user, 'TECH_DOC_VIEW')
    )
    if not allowed:
        return render(request, 'core/help_forbidden.html', status=403)
    from core.diagram_utils import diagram_context

    return render(request, 'core/help_document.html', {
        'doc_title': 'Technical Documentation',
        'doc_subtitle': 'Architecture, database, ERD, functional flow, and deployment',
        'doc_type': 'technical',
        'doc_icon': 'bi-code-slash',
        'doc_color': 'dark',
        **diagram_context(),
    })


@login_required
def help_diagrams(request):
    from core.diagram_utils import diagram_context

    return render(request, 'core/help_diagrams.html', diagram_context())


@login_required
def settings_hub(request):
    if not (
        request.user.is_superuser
        or is_admin_user(request.user)
        or user_has_permission(request.user, 'SETTINGS_MANAGE')
    ):
        return HttpResponseForbidden('Settings access requires administrator privileges.')

    from core.settings_registry import SETTINGS_SECTIONS

    return render(request, 'core/settings_hub.html', {
        'sections': SETTINGS_SECTIONS,
    })
