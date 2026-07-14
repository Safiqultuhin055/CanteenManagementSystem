from django.db import models
from employee.models import Employee, EmployeeCard
from users.models import User
from inventory.models import MenuItem, DailyFoodStock

class GuestCard(models.Model):
    card_number = models.CharField(max_length=100, unique=True)
    guest_name = models.CharField(max_length=300)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    guest_company = models.CharField(max_length=200, blank=True, null=True)
    host_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, db_column='host_employee_id')
    card_type = models.CharField(max_length=50, default='RFID')
    issued_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(blank=True, null=True)
    deposit_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    deposit_returned = models.BooleanField(default=False)
    loaded_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    used_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    card_status = models.CharField(max_length=20, default='ACTIVE')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'guest_cards'
        managed = False

    def __str__(self):
        return f"{self.card_number} - {self.guest_name}"


class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True)
    token_number = models.IntegerField()
    order_date = models.DateField(auto_now_add=True)
    order_time = models.DateTimeField(auto_now_add=True)
    order_type = models.CharField(max_length=20, default='EMPLOYEE')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, db_column='employee_id')
    employee_card = models.ForeignKey(EmployeeCard, on_delete=models.SET_NULL, null=True, blank=True, db_column='employee_card_id')
    guest_card = models.ForeignKey(GuestCard, on_delete=models.SET_NULL, null=True, blank=True, db_column='guest_card_id')
    customer_name = models.CharField(max_length=300, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, default='CARD')
    payment_status = models.CharField(max_length=20, default='PAID')
    order_status = models.CharField(max_length=20, default='PLACED')
    kitchen_status = models.CharField(max_length=20, default='PENDING')
    distribution_status = models.CharField(max_length=20, default='PENDING')
    advance_deducted = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    credit_deducted = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    cash_received = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    change_given = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    remarks = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='created_by',
        related_name='pos_orders_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'orders'
        managed = False

    def __str__(self):
        return f"Order {self.order_number}"


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, db_column='menu_item_id')
    daily_food_stock = models.ForeignKey(DailyFoodStock, on_delete=models.SET_NULL, null=True, blank=True, db_column='daily_food_stock_id')
    item_name = models.CharField(max_length=300)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=18, decimal_places=2)
    special_instructions = models.CharField(max_length=300, blank=True, null=True)
    item_status = models.CharField(max_length=20, default='ORDERED')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_details'
        managed = False

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"


class VoiceRequestLog(models.Model):
    """One turn of the Bangla voice assistant — what the customer asked and the
    order snapshot at that moment. Used to analyse demand (which products,
    which kinds of requests). Rows with ready_to_confirm=True are the strongest
    demand signal (a completed order intent)."""
    customer_name = models.CharField(max_length=300, blank=True, null=True)
    user_text = models.TextField(blank=True, null=True)
    reply_text = models.TextField(blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    item_count = models.IntegerField(default=0)
    qty_total = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    needs_more_info = models.BooleanField(default=False)
    ready_to_confirm = models.BooleanField(default=False)
    issues = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_request_logs'
        managed = False
        ordering = ('-created_at',)

    def __str__(self):
        return f"Voice #{self.pk}: {(self.user_text or '')[:40]}"


class VoiceRequestItem(models.Model):
    """A product line inside a voice turn — one row per menu item requested.
    GROUP BY menu_item_id to see which products customers ask for most."""
    voice_request_log = models.ForeignKey(
        VoiceRequestLog,
        on_delete=models.CASCADE,
        db_column='voice_request_log_id',
        related_name='items',
    )
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.SET_NULL, null=True, blank=True, db_column='menu_item_id'
    )
    item_name = models.CharField(max_length=300, blank=True, null=True)
    item_name_bn = models.CharField(max_length=300, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_request_items'
        managed = False

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"


class Payment(models.Model):
    payment_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    payment_method = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, default='COMPLETED')
    employee_card = models.ForeignKey(EmployeeCard, on_delete=models.SET_NULL, null=True, blank=True, db_column='employee_card_id')
    guest_card = models.ForeignKey(GuestCard, on_delete=models.SET_NULL, null=True, blank=True, db_column='guest_card_id')
    transaction_id = models.IntegerField(null=True, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.CharField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        managed = False

    def __str__(self):
        return f"Payment {self.payment_number}"
