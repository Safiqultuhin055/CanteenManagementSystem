from django.db import models
from pos.models import Order
from users.models import User

class KitchenQueue(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, db_column='order_id')
    token_number = models.IntegerField()
    queue_date = models.DateField(auto_now_add=True)
    queue_status = models.CharField(max_length=20, default='PENDING')
    priority = models.IntegerField(default=0)
    estimated_time_min = models.IntegerField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='assigned_to')
    remarks = models.CharField(max_length=300, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'kitchen_queue'
        managed = False

    def __str__(self):
        return f"Token {self.token_number} - {self.queue_status}"
