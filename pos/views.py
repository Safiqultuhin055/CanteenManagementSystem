import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from balance.models import EmployeeBalance
from employee.models import EmployeeCard
from inventory.models import FoodCategory, MenuItem

from .services.checkout import CheckoutError, process_checkout

logger = logging.getLogger(__name__)


@login_required
def pos_dashboard(request):
    categories = FoodCategory.objects.filter(is_active=True, is_deleted=False).order_by('category_name')
    menu_items = MenuItem.objects.filter(
        is_active=True, is_available=True, is_deleted=False
    ).select_related('category').order_by('category__category_name', 'item_name')
    return render(request, 'pos/pos_dashboard.html', {
        'categories': categories,
        'menu_items': menu_items,
    })


@login_required
@require_POST
def api_scan_card(request):
    try:
        data = json.loads(request.body)
        card_number = (data.get('card_number') or '').strip()
        if not card_number:
            return JsonResponse({'success': False, 'message': 'Card number required'})

        card = EmployeeCard.objects.select_related('employee', 'employee__department').filter(
            card_number=card_number,
            is_active=True,
            is_deleted=False,
            card_status='ACTIVE',
        ).first()

        if not card:
            return JsonResponse({'success': False, 'message': 'Invalid or inactive card'})

        employee = card.employee
        if not employee.is_active or employee.is_deleted:
            return JsonResponse({'success': False, 'message': 'Employee is inactive'})

        bal = EmployeeBalance.objects.filter(employee_id=employee.id).first()
        balance = float(bal.advance_balance) if bal else 0.0
        credit_limit = float((bal.credit_limit - bal.credit_used) if bal else 0)

        return JsonResponse({
            'success': True,
            'employee_name': employee.full_name,
            'department': employee.department.department_name,
            'balance': balance,
            'credit_limit': credit_limit,
            'card_id': card.id,
            'employee_id': employee.id,
            'card_number': card.card_number,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Card scan failed')
        return JsonResponse({'success': False, 'message': str(exc)})


@login_required
@require_POST
def api_checkout(request):
    try:
        data = json.loads(request.body)
        items = data.get('items') or {}
        card_id = data.get('card_id')
        employee_id = data.get('employee_id')
        is_guest = str(card_id).upper() == 'GUEST' or str(employee_id).upper() == 'GUEST'

        if not is_guest and (not card_id or not employee_id):
            return JsonResponse({'success': False, 'message': 'Scan employee card or enable guest mode'})

        result = process_checkout(
            items_raw=items,
            card_id=card_id,
            employee_id=employee_id,
            user_id=request.user.pk,
            is_guest=is_guest,
        )
        return JsonResponse(result)
    except CheckoutError as exc:
        return JsonResponse({'success': False, 'message': str(exc)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'})
    except Exception as exc:
        logger.exception('Checkout failed')
        return JsonResponse({'success': False, 'message': f'Checkout failed: {exc}'})
