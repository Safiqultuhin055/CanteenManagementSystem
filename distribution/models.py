from django.db import models
from pos.models import Order
from users.models import User

class DistributionQueue(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, db_column='order_id')
    token_number = models.IntegerField()
    queue_date = models.DateField(auto_now_add=True)
    queue_status = models.CharField(max_length=20, default='PENDING')
    called_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    counter_number = models.IntegerField(null=True, blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='handled_by')
    remarks = models.CharField(max_length=300, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'distribution_queue'
        managed = False

    def __str__(self):
        return f"Token {self.token_number} - {self.queue_status}"

class TokenStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    token_number = models.IntegerField()
    status_from = models.CharField(max_length=30, null=True, blank=True)
    status_to = models.CharField(max_length=30)
    status_type = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='changed_by')
    remarks = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'token_status_history'
        managed = False

    def __str__(self):
        return f"Token {self.token_number}: {self.status_from} -> {self.status_to}"
