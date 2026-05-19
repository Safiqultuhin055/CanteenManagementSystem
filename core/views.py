import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from core.dashboard_services import get_dashboard_data
from users.permissions import is_admin_user, user_has_permission

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    db_error = None
    try:
        connection.ensure_connection()
    except Exception as exc:
        db_error = str(exc)
        logger.exception('Dashboard database connection failed')

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = 'Good morning'
    elif hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'

    data = get_dashboard_data() if not db_error else {}
    fetch_error = data.pop('fetch_error', None) if data else None

    stats_empty = (
        not db_error
        and not fetch_error
        and data.get('employee_count', 0) == 0
        and data.get('menu_item_count', 0) == 0
        and data.get('order_count_today', 0) == 0
    )

    ctx = {
        **data,
        'greeting': greeting,
        'db_error': db_error or fetch_error,
        'stats_empty': stats_empty,
        'debug': settings.DEBUG,
    }
    return render(request, 'core/dashboard.html', ctx)


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
