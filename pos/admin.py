from django.contrib import admin

from core.admin_base import CanteenModelAdmin, CanteenTabularInline
from core.admin_forms import (
    GuestCardAdminForm,
    OrderAdminForm,
    OrderDetailAdminForm,
    PaymentAdminForm,
)
from .models import (
    GuestCard,
    Order,
    OrderDetail,
    Payment,
    VoiceRequestItem,
    VoiceRequestLog,
)


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


class VoiceRequestItemInline(CanteenTabularInline):
    model = VoiceRequestItem
    extra = 0
    autocomplete_all_relations = False
    fields = ('item_name', 'item_name_bn', 'quantity', 'unit_price', 'line_total')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(VoiceRequestLog)
class VoiceRequestLogAdmin(CanteenModelAdmin):
    """Read-only log of what customers asked the voice assistant — for demand
    analysis (which products, which kinds of requests)."""
    autocomplete_all_relations = False
    list_display = (
        'created_at', 'customer_name', 'user_text', 'qty_total',
        'subtotal', 'ready_to_confirm', 'needs_more_info', 'provider',
    )
    list_filter = ('ready_to_confirm', 'needs_more_info', 'provider', 'created_at')
    search_fields = ('customer_name', 'user_text', 'reply_text')
    date_hierarchy = 'created_at'
    inlines = [VoiceRequestItemInline]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
