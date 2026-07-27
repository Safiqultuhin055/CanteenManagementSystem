from django.db import models

from core.model_display import name_with_code

class Department(models.Model):
    department_name = models.CharField(max_length=200, unique=True)
    department_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    head_employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='head_employee_id',
        related_name='headed_departments',
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'departments'
        managed = False

    def __str__(self):
        return name_with_code(self.department_name, self.department_code)

class Employee(models.Model):
    employee_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=300)
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, db_column='department_id')
    designation = models.CharField(max_length=200, blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_leaving = models.DateField(blank=True, null=True)
    employee_type = models.CharField(max_length=50, default='PERMANENT')
    profile_image = models.CharField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'employees'
        managed = False

    def __str__(self):
        return name_with_code(self.full_name, self.employee_code)

class FaceEmbedding(models.Model):
    """One registered face per employee (128-d face-api.js descriptor as JSON)."""
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, db_column='employee_id',
        related_name='face_embedding',
    )
    embedding = models.TextField()  # JSON array of 128 floats
    model = models.CharField(max_length=50, default='face-api-128')
    sample_count = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'face_embeddings'
        managed = False

    def __str__(self):
        return f'Face — {self.employee}'


class EmployeeCard(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id')
    card_number = models.CharField(max_length=100, unique=True)
    card_type = models.CharField(max_length=50, default='RFID')
    issued_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    card_status = models.CharField(max_length=20, default='ACTIVE')
    deactivated_at = models.DateTimeField(blank=True, null=True)
    deactivation_reason = models.CharField(max_length=200, blank=True, null=True)
    replaced_by_card_id = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'employee_cards'
        managed = False

    def __str__(self):
        return f'{self.card_number} - {self.employee}'
