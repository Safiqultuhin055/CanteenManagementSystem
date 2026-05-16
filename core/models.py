from django.db import models


class SystemSetting(models.Model):
    setting_key = models.CharField(max_length=200, unique=True)
    setting_value = models.CharField(max_length=2000)
    setting_type = models.CharField(max_length=50, default='STRING')
    category = models.CharField(max_length=100, default='GENERAL')
    description = models.CharField(max_length=500, blank=True, null=True)
    is_editable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'system_settings'
        managed = False
        verbose_name = 'System setting'
        verbose_name_plural = 'System settings'

    def __str__(self):
        return self.setting_key


class AuditLog(models.Model):
    user_id = models.IntegerField(blank=True, null=True, db_column='user_id')
    username = models.CharField(max_length=150, blank=True, null=True)
    action = models.CharField(max_length=50)
    table_name = models.CharField(max_length=200, blank=True, null=True)
    record_id = models.IntegerField(blank=True, null=True)
    old_values = models.TextField(blank=True, null=True)
    new_values = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    module = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'audit_logs'
        managed = False
        verbose_name = 'Audit log'
        verbose_name_plural = 'Audit logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.table_name or self.module}'
