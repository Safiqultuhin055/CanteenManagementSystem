"""Shared Django admin configuration for CanteenSys."""
from django.contrib import admin
from django.db import models

FORM_CONTROL = {'class': 'vTextField cms-input'}
FORM_SELECT = {'class': 'cms-select'}
FORM_TEXTAREA = {'class': 'vLargeTextField cms-input', 'rows': 3}
FORM_CHECK = {'class': 'cms-check'}
FORM_NUMBER = {'class': 'vIntegerField cms-input'}

_SEARCH_SKIP = frozenset({
    'password', 'password_hash', 'profile_image', 'description', 'address',
    'remarks', 'special_instructions', 'icon_class', 'url',
})
_SEARCH_PRIORITY = (
    'employee_code', 'full_name', 'first_name', 'last_name',
    'item_code', 'item_name', 'material_code', 'material_name',
    'category_code', 'category_name', 'department_code', 'department_name',
    'role_code', 'role_name', 'permission_code', 'permission_name',
    'menu_code', 'menu_name', 'card_number', 'order_number', 'supplier_name',
    'username', 'email', 'phone', 'guest_name', 'transaction_number',
    'payment_number', 'reference_number',
)


def default_admin_search_fields(model):
    """Build search_fields for autocomplete when not set on ModelAdmin."""
    names = []
    for f in model._meta.fields:
        if isinstance(f, models.CharField):
            if f.name in _SEARCH_SKIP or (f.max_length and f.max_length > 500):
                continue
            names.append(f.name)
        elif isinstance(f, models.IntegerField) and f.name in (
            'token_number', 'id', 'employee_id',
        ):
            names.append(f.name)

    ordered = []
    for key in _SEARCH_PRIORITY:
        if key in names:
            ordered.append(key)
    for name in names:
        if name not in ordered:
            ordered.append(name)
    return tuple(ordered[:10])


def foreign_key_field_names(model):
    return [
        f.name
        for f in model._meta.fields
        if isinstance(f, (models.ForeignKey, models.OneToOneField))
    ]


class CanteenModelAdmin(admin.ModelAdmin):
    """Base admin with soft-delete filters, searchable FK widgets, and audit fields."""

    save_on_top = True
    list_per_page = 25
    show_full_result_count = False
    change_list_template = 'admin/cms_change_list.html'
    change_form_template = 'admin/cms_change_form.html'
    autocomplete_all_relations = True

    def get_search_fields(self, request):
        if self.search_fields:
            return self.search_fields
        return default_admin_search_fields(self.model)

    def get_autocomplete_fields(self, request):
        if not self.autocomplete_all_relations:
            return super().get_autocomplete_fields(request)
        explicit = getattr(self.__class__, 'autocomplete_fields', None)
        if explicit is not None and len(explicit) > 0:
            return explicit
        return tuple(foreign_key_field_names(self.model))

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            for name in ('created_at', 'updated_at', 'created_by', 'updated_by'):
                if hasattr(self.model, name) and name not in readonly:
                    readonly.append(name)
        return readonly

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.model, 'is_deleted'):
            return qs.filter(is_deleted=False)
        return qs


class CanteenTabularInline(admin.TabularInline):
    autocomplete_all_relations = True

    def get_autocomplete_fields(self, request):
        if not self.autocomplete_all_relations:
            return super().get_autocomplete_fields(request)
        explicit = getattr(self.__class__, 'autocomplete_fields', None)
        if explicit is not None and len(explicit) > 0:
            return explicit
        return tuple(foreign_key_field_names(self.model))


class CanteenStackedInline(admin.StackedInline):
    autocomplete_all_relations = True

    def get_autocomplete_fields(self, request):
        if not self.autocomplete_all_relations:
            return super().get_autocomplete_fields(request)
        explicit = getattr(self.__class__, 'autocomplete_fields', None)
        if explicit is not None and len(explicit) > 0:
            return explicit
        return tuple(foreign_key_field_names(self.model))


def setup_admin_site():
    admin.site.site_header = 'CanteenSys Administration'
    admin.site.site_title = 'CanteenSys Admin'
    admin.site.index_title = 'Settings & master data'
