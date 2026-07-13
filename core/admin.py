from django.contrib import admin

from core.admin_base import CanteenModelAdmin
from core.admin_forms import ApiIntegrationAdminForm, AuditLogAdminForm, SystemSettingAdminForm
from core.api_registry import invalidate as invalidate_api_cache
from core.models import ApiIntegration, AuditLog, SystemSetting


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


@admin.register(ApiIntegration)
class ApiIntegrationAdmin(CanteenModelAdmin):
    form = ApiIntegrationAdminForm
    list_display = ('label', 'provider', 'api_model', 'key_masked', 'is_default', 'is_active')
    list_filter = ('provider', 'is_active', 'is_default')
    search_fields = ('label', 'provider', 'api_model')
    fieldsets = (
        (None, {'fields': ('provider', 'label', 'is_default', 'is_active')}),
        ('Credentials', {'fields': ('api_key', 'api_model', 'base_url')}),
        ('Advanced', {'fields': ('extra_config',)}),
    )

    @admin.display(description='API key')
    def key_masked(self, obj):
        return obj.key_masked

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        invalidate_api_cache(obj.provider)

    def delete_model(self, request, obj):
        provider = obj.provider
        super().delete_model(request, obj)
        invalidate_api_cache(provider)

    def delete_queryset(self, request, queryset):
        providers = list(queryset.values_list('provider', flat=True).distinct())
        super().delete_queryset(request, queryset)
        for p in providers:
            invalidate_api_cache(p)


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
