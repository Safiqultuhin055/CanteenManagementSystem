from django.contrib import admin

from core.admin_base import CanteenModelAdmin
from core.admin_forms import (
    BalanceAllocationAdminForm,
    CardTransactionAdminForm,
    CreditLimitAdminForm,
    EmployeeBalanceAdminForm,
    MonthlyAllowanceAdminForm,
)
from .models import (
    BalanceAllocation, CardTransaction, CreditLimit,
    EmployeeBalance, MonthlyAllowance,
)


@admin.register(EmployeeBalance)
class EmployeeBalanceAdmin(CanteenModelAdmin):
    form = EmployeeBalanceAdminForm
    list_display = ('employee', 'advance_balance', 'credit_limit', 'credit_used', 'total_spent')
    search_fields = ('employee__full_name', 'employee__employee_code')


@admin.register(BalanceAllocation)
class BalanceAllocationAdmin(CanteenModelAdmin):
    form = BalanceAllocationAdminForm
    list_display = ('employee', 'allocation_type', 'amount', 'allocation_date', 'balance_after')
    list_filter = ('allocation_type',)
    search_fields = ('employee__full_name', 'employee__employee_code', 'reference_number')


@admin.register(MonthlyAllowance)
class MonthlyAllowanceAdmin(CanteenModelAdmin):
    form = MonthlyAllowanceAdminForm
    list_display = ('allowance_month', 'allowance_year', 'department', 'amount_per_employee', 'allocation_status')
    list_filter = ('allocation_status', 'allowance_year')


@admin.register(CreditLimit)
class CreditLimitAdmin(CanteenModelAdmin):
    form = CreditLimitAdminForm
    list_display = ('employee', 'new_limit', 'approval_status', 'approved_at')
    list_filter = ('approval_status',)
    search_fields = ('employee__full_name', 'employee__employee_code', 'reference_number')


@admin.register(CardTransaction)
class CardTransactionAdmin(CanteenModelAdmin):
    form = CardTransactionAdminForm
    list_display = ('transaction_number', 'employee', 'transaction_type', 'amount', 'transaction_date')
    list_filter = ('transaction_type',)
    search_fields = ('transaction_number',)
