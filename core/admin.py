from django.contrib import admin

from core.admin_base import CanteenModelAdmin
from core.admin_forms import AuditLogAdminForm, SystemSettingAdminForm
from core.models import AuditLog, SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(CanteenModelAdmin):
    form = SystemSettingAdminForm
    list_display = ('setting_key', 'setting_value', 'setting_type', 'category', 'is_active', 'is_editable')
    list_filter = ('category', 'setting_type', 'is_active')
    search_fields = ('setting_key', 'description')
    fieldsets = (
        (None, {'fields': ('setting_key', 'setting_value', 'setting_type', 'category')}),
        ('Details', {'fields': ('description', 'is_editable', 'is_active')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(CanteenModelAdmin):
    form = AuditLogAdminForm
    list_display = ('created_at', 'username', 'action', 'module', 'table_name', 'record_id')
    list_filter = ('action', 'module', 'created_at')
    search_fields = ('username', 'description', 'table_name')
    readonly_fields = (
        'user_id', 'username', 'action', 'table_name', 'record_id',
        'old_values', 'new_values', 'ip_address', 'user_agent', 'module',
        'description', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
