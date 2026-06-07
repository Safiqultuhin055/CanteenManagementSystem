from django.contrib import admin
from django.utils.html import format_html

from core.admin_base import CanteenModelAdmin
from core.admin_forms import (
    DailyFoodStockAdminForm,
    FoodCategoryAdminForm,
    MenuItemAdminForm,
    RawMaterialAdminForm,
    RawMaterialStockAdminForm,
    SupplierAdminForm,
    WasteRecordAdminForm,
)
from inventory.services.menu_image import save_menu_item_image_bytes
from .models import (
    DailyFoodStock, FoodCategory, MenuItem, RawMaterial,
    RawMaterialStock, Supplier, WasteRecord,
)


@admin.register(FoodCategory)
class FoodCategoryAdmin(CanteenModelAdmin):
    form = FoodCategoryAdminForm
    list_display = ('category_name', 'category_code', 'is_active')
    search_fields = ('category_name', 'category_code')


@admin.register(MenuItem)
class MenuItemAdmin(CanteenModelAdmin):
    form = MenuItemAdminForm
    list_display = (
        'thumb_preview', 'item_name', 'item_code', 'category',
        'unit_price', 'is_available', 'is_active',
    )
    list_filter = ('category', 'is_available', 'is_vegetarian')
    search_fields = ('item_name', 'item_code')
    readonly_fields = ('image_preview',)

    def get_queryset(self, request):
        from django.db.models import BooleanField, Case, Value, When
        qs = super().get_queryset(request)
        return qs.annotate(
            _has_image=Case(
                When(image_data__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).defer('image_data')

    fieldsets = (
        (None, {
            'fields': (
                'item_name', 'item_code', 'category', 'description',
                'unit_price', 'tax_rate', 'is_vegetarian',
            ),
        }),
        ('Image (POS menu)', {
            'fields': ('image_upload', 'image_preview'),
            'description': 'Image is stored in database (image_data BLOB), not in media folder.',
        }),
        ('Status', {
            'fields': ('is_available', 'is_active'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        upload = form.cleaned_data.get('image_upload')
        if upload:
            content_type = getattr(upload, 'content_type', None) or 'image/png'
            save_menu_item_image_bytes(obj, upload.read(), content_type)

    @admin.display(description='Photo')
    def thumb_preview(self, obj):
        if obj and obj.has_image:
            return format_html(
                '<img src="{}" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:6px;">',
                obj.get_image_url(),
            )
        return '—'

    @admin.display(description='Current image')
    def image_preview(self, obj):
        if obj and obj.has_image:
            return format_html(
                '<img src="{}" alt="" style="max-width:280px;max-height:200px;border-radius:8px;object-fit:cover;">',
                obj.get_image_url(),
            )
        return format_html('<span style="color:#888;">No image — POS shows a placeholder icon.</span>')


@admin.register(Supplier)
class SupplierAdmin(CanteenModelAdmin):
    form = SupplierAdminForm
    list_display = ('supplier_name', 'contact_person', 'phone', 'is_active')
    search_fields = ('supplier_name',)


@admin.register(RawMaterial)
class RawMaterialAdmin(CanteenModelAdmin):
    form = RawMaterialAdminForm
    list_display = ('material_name', 'material_code', 'category', 'unit_of_measure')
    search_fields = ('material_name', 'material_code')


@admin.register(RawMaterialStock)
class RawMaterialStockAdmin(CanteenModelAdmin):
    form = RawMaterialStockAdminForm
    list_display = ('raw_material', 'current_quantity', 'last_purchase_price')


@admin.register(DailyFoodStock)
class DailyFoodStockAdmin(CanteenModelAdmin):
    form = DailyFoodStockAdminForm
    list_display = ('menu_item', 'stock_date', 'prepared_quantity', 'sold_quantity', 'is_available')
    list_filter = ('stock_date', 'is_available')


@admin.register(WasteRecord)
class WasteRecordAdmin(CanteenModelAdmin):
    form = WasteRecordAdminForm
    list_display = ('waste_date', 'waste_type', 'waste_reason', 'quantity', 'estimated_cost')
    list_filter = ('waste_type', 'waste_date')
