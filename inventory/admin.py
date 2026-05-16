from django.contrib import admin

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
    list_display = ('item_name', 'item_code', 'category', 'unit_price', 'is_available', 'is_active')
    list_filter = ('category', 'is_available', 'is_vegetarian')
    search_fields = ('item_name', 'item_code')


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
