from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.admin_base import CanteenModelAdmin, CanteenTabularInline
from core.admin_forms import (
    CanteenUserChangeForm,
    CanteenUserCreationForm,
    MenuAdminForm,
    MenuPermissionAdminForm,
    PermissionAdminForm,
    RoleAdminForm,
    RolePermissionAdminForm,
    UserRoleAdminForm,
)
from .models import Menu, MenuPermission, Permission, Role, RolePermission, User, UserRole


@admin.register(Role)
class RoleAdmin(CanteenModelAdmin):
    form = RoleAdminForm
    list_display = ('role_name', 'role_code', 'priority', 'is_active')
    search_fields = ('role_name', 'role_code')
    list_filter = ('is_active',)
    fieldsets = (
        (None, {'fields': ('role_name', 'role_code', 'description', 'priority', 'is_active')}),
    )


@admin.register(Permission)
class PermissionAdmin(CanteenModelAdmin):
    form = PermissionAdminForm
    list_display = ('permission_name', 'permission_code', 'module', 'is_active')
    search_fields = ('permission_name', 'permission_code', 'module')
    list_filter = ('module', 'is_active')


@admin.register(Menu)
class MenuAdmin(CanteenModelAdmin):
    form = MenuAdminForm
    list_display = ('menu_name', 'menu_code', 'parent', 'url', 'display_order', 'menu_level', 'is_visible')
    list_filter = ('menu_level', 'is_visible', 'is_active')
    search_fields = ('menu_name', 'menu_code')
    ordering = ('menu_level', 'display_order')


@admin.register(MenuPermission)
class MenuPermissionAdmin(CanteenModelAdmin):
    form = MenuPermissionAdminForm
    list_display = ('menu', 'permission', 'is_active')
    list_filter = ('is_active',)


@admin.register(RolePermission)
class RolePermissionAdmin(CanteenModelAdmin):
    form = RolePermissionAdminForm
    list_display = ('role', 'permission', 'is_active')
    list_filter = ('role', 'is_active')


class UserRoleInline(CanteenTabularInline):
    model = UserRole
    form = UserRoleAdminForm
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CanteenUserChangeForm
    add_form = CanteenUserCreationForm
    model = User
    filter_horizontal = ()
    list_display = ('username', 'email', 'full_name', 'employee', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'full_name', 'employee__employee_code', 'employee__full_name')
    autocomplete_fields = ('employee',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'full_name', 'email', 'phone', 'employee')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_deleted')}),
        ('Security', {'fields': ('must_change_password', 'failed_login_count', 'locked_until')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'full_name', 'is_staff', 'is_active'),
        }),
    )
    inlines = [UserRoleInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(UserRole)
class UserRoleAdmin(CanteenModelAdmin):
    form = UserRoleAdminForm
    list_display = ('user', 'role', 'is_active')
    list_filter = ('role', 'is_active')
