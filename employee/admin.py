from django.contrib import admin

from core.admin_base import CanteenModelAdmin
from core.admin_forms import DepartmentAdminForm, EmployeeAdminForm, EmployeeCardAdminForm
from .models import Department, Employee, EmployeeCard


@admin.register(Department)
class DepartmentAdmin(CanteenModelAdmin):
    form = DepartmentAdminForm
    list_display = ('department_name', 'department_code', 'is_active')
    search_fields = ('department_name', 'department_code')
    list_filter = ('is_active',)
    fieldsets = (
        (None, {'fields': ('department_name', 'department_code', 'description', 'head_employee', 'is_active')}),
    )


@admin.register(Employee)
class EmployeeAdmin(CanteenModelAdmin):
    form = EmployeeAdminForm
    list_display = ('employee_code', 'full_name', 'department', 'designation', 'is_active')
    search_fields = ('employee_code', 'full_name', 'email', 'phone')
    list_filter = ('department', 'is_active', 'employee_type')
    fieldsets = (
        ('Identity', {'fields': ('employee_code', 'first_name', 'last_name', 'full_name')}),
        ('Work', {'fields': ('department', 'designation', 'employee_type', 'date_of_joining', 'date_of_leaving')}),
        ('Contact', {'fields': ('email', 'phone', 'address', 'emergency_contact')}),
        ('Status', {'fields': ('profile_image', 'is_active')}),
    )


@admin.register(EmployeeCard)
class EmployeeCardAdmin(CanteenModelAdmin):
    form = EmployeeCardAdminForm
    list_display = ('card_number', 'employee', 'card_type', 'card_status', 'issued_date')
    search_fields = ('card_number', 'employee__full_name')
    list_filter = ('card_status', 'card_type')
