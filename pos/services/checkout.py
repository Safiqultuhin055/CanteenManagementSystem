import logging
from decimal import Decimal

from django.db import connection, transaction
from django.db.utils import IntegrityError
from django.utils import timezone

from core.business_date import get_business_date

from balance.models import CardTransaction, EmployeeBalance
from employee.models import EmployeeCard
from inventory.models import DailyFoodStock, MenuItem
from kitchen.models import KitchenQueue
from kitchen.realtime import notify_kitchen_queue_changed
from pos.models import Order, OrderDetail, Payment
from pos.services.receipt_settings import get_receipt_settings

logger = logging.getLogger(__name__)


class CheckoutError(Exception):
    pass


def _next_seq(name):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT NEXT VALUE FOR dbo.{name}')
        return cursor.fetchone()[0]


def _next_order_number():
    seq = _next_seq('seq_order')
    return f"ORD-{timezone.now().strftime('%Y%m%d')}-{seq:04d}"


def _next_payment_number():
    seq = _next_seq('seq_payment')
    return f"PAY-{timezone.now().strftime('%Y%m%d')}-{seq:04d}"


def _next_transaction_number():
    seq = _next_seq('seq_transaction')
    return f"TXN-{timezone.now().strftime('%Y%m%d')}-{seq:04d}"


def _next_token(sale_date):
    """
    Next daily token under UQ_orders_token_date (token_number + order_date).
    Includes soft-deleted rows and locks to avoid duplicate tokens on concurrent sales.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ISNULL(MAX([token_number]), 0) + 1
            FROM [dbo].[orders] WITH (UPDLOCK, HOLDLOCK)
            WHERE [order_date] = %s
            """,
            [sale_date],
        )
        return int(cursor.fetchone()[0])


def _parse_cart(items_raw):
    if not items_raw:
        raise CheckoutError('Cart is empty')

    lines = []
    for key, row in items_raw.items():
        try:
            menu_item_id = int(key)
        except (TypeError, ValueError):
            raise CheckoutError('Invalid menu item in cart')
        qty = int(row.get('qty') or 0)
        if qty <= 0:
            continue
        lines.append({
            'menu_item_id': menu_item_id,
            'qty': qty,
            'client_price': Decimal(str(row.get('price', 0))),
            'client_name': row.get('name') or '',
        })

    if not lines:
        raise CheckoutError('Cart is empty')
    return lines


def _load_line_items(lines, stock_date):
    result = []
    subtotal = Decimal('0')

    for line in lines:
        menu_item = MenuItem.objects.filter(
            pk=line['menu_item_id'], is_active=True, is_deleted=False
        ).first()
        if not menu_item:
            raise CheckoutError(f"Menu item #{line['menu_item_id']} not found")

        stock = DailyFoodStock.objects.filter(
            menu_item_id=menu_item.id,
            stock_date=stock_date,
            is_deleted=False,
            is_available=True,
        ).first()

        unit_price = menu_item.unit_price
        if stock:
            if stock.expired_date and stock.expired_date < stock_date:
                raise CheckoutError(f"{menu_item.item_name} is expired")
            remaining = stock.prepared_quantity - stock.sold_quantity - stock.waste_quantity
            if remaining < line['qty']:
                raise CheckoutError(
                    f"Insufficient stock for {menu_item.item_name} (only {remaining} left)"
                )
            unit_price = stock.unit_price

        tax_rate = menu_item.tax_rate or Decimal('0')
        line_subtotal = unit_price * line['qty']
        tax_amount = (line_subtotal * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
        line_total = line_subtotal + tax_amount
        subtotal += line_total

        result.append({
            'menu_item': menu_item,
            'stock': stock,
            'qty': line['qty'],
            'unit_price': unit_price,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'line_subtotal': line_subtotal,
            'line_total': line_total,
        })

    return result, subtotal


def _deduct_balance(employee_id, total):
    bal = EmployeeBalance.objects.select_for_update().filter(employee_id=employee_id).first()
    if not bal:
        raise CheckoutError('Employee balance record not found')

    advance = bal.advance_balance or Decimal('0')
    credit_available = (bal.credit_limit or Decimal('0')) - (bal.credit_used or Decimal('0'))
    remaining = total
    deduct_adv = Decimal('0')
    deduct_cred = Decimal('0')

    if advance >= remaining:
        deduct_adv = remaining
        remaining = Decimal('0')
    else:
        deduct_adv = advance
        remaining -= advance
        if credit_available >= remaining:
            deduct_cred = remaining
            remaining = Decimal('0')
        else:
            raise CheckoutError('Insufficient balance and credit limit')

    bal.advance_balance = advance - deduct_adv
    bal.credit_used = (bal.credit_used or Decimal('0')) + deduct_cred
    bal.total_spent = (bal.total_spent or Decimal('0')) + total
    bal.last_transaction_at = timezone.now()
    bal.save(update_fields=[
        'advance_balance', 'credit_used', 'total_spent', 'last_transaction_at', 'updated_at',
    ])
    return deduct_adv, deduct_cred, bal


def process_checkout(*, items_raw, card_id, employee_id, user_id, is_guest=False):
    lines = _parse_cart(items_raw)
    sale_date = get_business_date()
    line_items, total = _load_line_items(lines, sale_date)
    tax_total = sum((li['tax_amount'] for li in line_items), Decimal('0'))
    subtotal = total - tax_total

    last_error = None
    for attempt in range(3):
        try:
            return _commit_checkout(
                line_items=line_items,
                sale_date=sale_date,
                subtotal=subtotal,
                tax_total=tax_total,
                total=total,
                card_id=card_id,
                employee_id=employee_id,
                user_id=user_id,
                is_guest=is_guest,
            )
        except IntegrityError as exc:
            last_error = exc
            if 'UQ_orders_token_date' not in str(exc) and 'token' not in str(exc).lower():
                raise CheckoutError(f'Checkout failed: {exc}') from exc
            logger.warning('Token collision on attempt %s, retrying', attempt + 1)
    raise CheckoutError(
        'Could not assign a token number. Please try again.'
    ) from last_error


def _commit_checkout(
    *,
    line_items,
    sale_date,
    subtotal,
    tax_total,
    total,
    card_id,
    employee_id,
    user_id,
    is_guest,
):
    with transaction.atomic():
        token_number = _next_token(sale_date)
        order_number = _next_order_number()
        order_type = 'CASH' if is_guest else 'EMPLOYEE'
        payment_method = 'CASH' if is_guest else 'CARD'

        employee = None
        card = None
        deduct_adv = Decimal('0')
        deduct_cred = Decimal('0')
        customer_name = None

        if is_guest:
            customer_name = 'Guest Customer'
        else:
            try:
                card_pk = int(card_id)
                emp_pk = int(employee_id)
            except (TypeError, ValueError):
                raise CheckoutError('Invalid card or employee')

            card = EmployeeCard.objects.select_related('employee').filter(
                pk=card_pk, is_active=True, card_status='ACTIVE', is_deleted=False,
            ).first()
            if not card or card.employee_id != emp_pk:
                raise CheckoutError('Invalid or inactive card')
            employee = card.employee
            deduct_adv, deduct_cred, _bal = _deduct_balance(emp_pk, total)

        order = Order.objects.create(
            order_number=order_number,
            token_number=token_number,
            order_date=sale_date,
            order_type=order_type,
            employee=employee,
            employee_card=card,
            customer_name=customer_name,
            subtotal=subtotal,
            tax_amount=tax_total,
            total_amount=total,
            payment_method=payment_method,
            payment_status='PAID',
            order_status='CONFIRMED',
            kitchen_status='PENDING',
            distribution_status='PENDING',
            advance_deducted=deduct_adv,
            credit_deducted=deduct_cred,
            created_by_id=user_id,
        )

        for li in line_items:
            menu_item = li['menu_item']
            OrderDetail.objects.create(
                order=order,
                menu_item=menu_item,
                daily_food_stock=li['stock'],
                item_name=menu_item.item_name,
                quantity=li['qty'],
                unit_price=li['unit_price'],
                tax_rate=li['tax_rate'],
                tax_amount=li['tax_amount'],
                total_price=li['line_total'],
            )
            if li['stock']:
                stock = li['stock']
                stock.sold_quantity = (stock.sold_quantity or 0) + li['qty']
                stock.save(update_fields=['sold_quantity', 'updated_at'])

        KitchenQueue.objects.create(
            order=order,
            token_number=token_number,
            queue_date=sale_date,
            queue_status='PENDING',
        )
        transaction.on_commit(notify_kitchen_queue_changed)

        payment = Payment.objects.create(
            payment_number=_next_payment_number(),
            order=order,
            payment_method=payment_method,
            amount=total,
            payment_status='COMPLETED',
            employee_card=card,
        )

        if employee and card:
            bal_after = EmployeeBalance.objects.get(employee_id=employee.id)
            CardTransaction.objects.create(
                transaction_number=_next_transaction_number(),
                employee=employee,
                card=card,
                transaction_type='SALE_DEBIT',
                amount=total,
                advance_balance_before=(bal_after.advance_balance or Decimal('0')) + deduct_adv,
                advance_balance_after=bal_after.advance_balance,
                credit_used_before=(bal_after.credit_used or Decimal('0')) - deduct_cred,
                credit_used_after=bal_after.credit_used,
                order_id=order.id,
                payment_id=payment.id,
                created_by=user_id,
                remarks=f'POS order {order_number}',
            )

        item_summary = [
            {
                'name': li['menu_item'].item_name,
                'qty': li['qty'],
                'unit_price': float(li['unit_price']),
                'line_total': float(li['line_total']),
            }
            for li in line_items
        ]
        qty_total = sum(li['qty'] for li in line_items)
        display_customer = customer_name or (
            employee.full_name if employee else 'Guest Customer'
        )
        cashier = ''
        if user_id:
            from users.models import User
            cashier_user = User.objects.filter(pk=user_id).only('username', 'full_name').first()
            if cashier_user:
                cashier = cashier_user.full_name or cashier_user.username

        return {
            'success': True,
            'message': (
                f'Order placed — Token #{token_number} '
                f'({len(line_items)} item type(s), {qty_total} pcs)'
            ),
            'order_number': order_number,
            'token_number': token_number,
            'total_amount': float(total),
            'item_count': len(line_items),
            'quantity_total': qty_total,
            'items': item_summary,
            'receipt': {
                **get_receipt_settings(),
                'order_number': order_number,
                'token_number': token_number,
                'barcode': order_number,
                'order_date': str(sale_date),
                'order_time': timezone.now().strftime('%d %b %Y, %I:%M %p'),
                'customer_name': display_customer,
                'payment_method': 'Cash' if is_guest else 'Card',
                'cashier': cashier,
                'subtotal': float(subtotal),
                'tax_amount': float(tax_total),
                'total_amount': float(total),
                'quantity_total': qty_total,
                'items': item_summary,
            },
        }
