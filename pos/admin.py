from django.contrib import admin

from core.admin_base import CanteenModelAdmin, CanteenTabularInline
from core.admin_forms import (
    GuestCardAdminForm,
    OrderAdminForm,
    OrderDetailAdminForm,
    PaymentAdminForm,
)
from .models import GuestCard, Order, OrderDetail, Payment


class OrderDetailInline(CanteenTabularInline):
    model = OrderDetail
    form = OrderDetailAdminForm
    extra = 0


@admin.register(Order)
class OrderAdmin(CanteenModelAdmin):
    form = OrderAdminForm
    list_display = ('order_number', 'token_number', 'order_date', 'order_type', 'total_amount', 'order_status')
    list_filter = ('order_type', 'order_status', 'payment_status', 'order_date')
    search_fields = ('order_number', 'token_number', 'customer_name')
    inlines = [OrderDetailInline]


@admin.register(Payment)
class PaymentAdmin(CanteenModelAdmin):
    form = PaymentAdminForm
    list_display = ('payment_number', 'order', 'payment_method', 'amount', 'payment_status')
    search_fields = ('payment_number', 'order__order_number')


@admin.register(GuestCard)
class GuestCardAdmin(CanteenModelAdmin):
    form = GuestCardAdminForm
    list_display = ('card_number', 'guest_name', 'loaded_balance', 'used_balance', 'card_status')
    search_fields = ('card_number', 'guest_name')
