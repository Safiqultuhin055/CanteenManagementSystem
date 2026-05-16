from django.db import models
from users.models import User
from employee.models import Employee, Department, EmployeeCard

class EmployeeBalance(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, db_column='employee_id')
    advance_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    credit_used = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    total_allocated = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    last_transaction_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_balances'
        managed = False

    def __str__(self):
        return f"{self.employee.full_name} - Balance: {self.advance_balance}"

class BalanceAllocation(models.Model):
    ALLOCATION_TYPES = [
        ('ADVANCE_TOPUP', 'Advance Topup'),
        ('MONTHLY_ALLOWANCE', 'Monthly Allowance'),
        ('CREDIT_ADJUSTMENT', 'Credit Adjustment'),
        ('REFUND', 'Refund'),
        ('MANUAL_ADJUSTMENT', 'Manual Adjustment'),
        ('OPENING_BALANCE', 'Opening Balance'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id')
    allocation_type = models.CharField(max_length=50, choices=ALLOCATION_TYPES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance_before = models.DecimalField(max_digits=18, decimal_places=2)
    balance_after = models.DecimalField(max_digits=18, decimal_places=2)
    allocation_date = models.DateField(auto_now_add=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.CharField(max_length=500, blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='approved_by', related_name='approved_allocations')
    approved_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'balance_allocations'
        managed = False

    def __str__(self):
        return f"{self.employee.full_name} - {self.allocation_type} : {self.amount}"

class MonthlyAllowance(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    allowance_month = models.IntegerField()
    allowance_year = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, db_column='department_id')
    amount_per_employee = models.DecimalField(max_digits=18, decimal_places=2)
    total_employees = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    allocation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    allocated_at = models.DateTimeField(blank=True, null=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='allocated_by', related_name='allocated_monthly_allowances')
    remarks = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'monthly_allowances'
        managed = False

    def __str__(self):
        return f"Monthly Allowance - {self.allowance_month}/{self.allowance_year}"

class CreditLimit(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id')
    previous_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    new_limit = models.DecimalField(max_digits=18, decimal_places=2)
    effective_from = models.DateField(auto_now_add=True)
    effective_to = models.DateField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='approved_by', related_name='approved_credit_limits')
    approved_at = models.DateTimeField(blank=True, null=True)
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.CharField(max_length=500, blank=True, null=True)
    remarks = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'credit_limits'
        managed = False

    def __str__(self):
        return f"Credit Limit {self.new_limit} for {self.employee.full_name}"

class CardTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE_DEBIT', 'Sale Debit'),
        ('ADVANCE_TOPUP', 'Advance Topup'),
        ('MONTHLY_ALLOWANCE', 'Monthly Allowance'),
        ('CREDIT_DEBIT', 'Credit Debit'),
        ('REFUND', 'Refund'),
        ('MANUAL_ADJUSTMENT', 'Manual Adjustment'),
        ('CASH_SALE', 'Cash Sale'),
    ]
    transaction_number = models.CharField(max_length=50, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, db_column='employee_id')
    card = models.ForeignKey(EmployeeCard, on_delete=models.SET_NULL, null=True, blank=True, db_column='card_id')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    advance_balance_before = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    advance_balance_after = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    credit_used_before = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    credit_used_after = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    order_id = models.IntegerField(null=True, blank=True)
    payment_id = models.IntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'card_transactions'
        managed = False

    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_type}"
