from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from core.model_display import name_with_code

class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)
    role_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'roles'
        managed = False

    def __str__(self):
        return name_with_code(self.role_name, self.role_code)

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=256, db_column='password_hash')
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='employee_id',
        related_name='user_accounts',
    )
    
    profile_image = models.CharField(max_length=500, blank=True, null=True)
    
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    must_change_password = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(blank=True, null=True)
    
    failed_login_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    roles = models.ManyToManyField(Role, through='UserRole', related_name='users')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return name_with_code(self.full_name or self.username, self.username)

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_roles'
        managed = False


class Permission(models.Model):
    permission_name = models.CharField(max_length=200)
    permission_code = models.CharField(max_length=100, unique=True)
    module = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'permissions'
        managed = False

    def __str__(self):
        return name_with_code(self.permission_name, self.permission_code)


class Menu(models.Model):
    menu_name = models.CharField(max_length=200)
    menu_code = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, db_column='parent_id'
    )
    url = models.CharField(max_length=500, blank=True, null=True)
    icon_class = models.CharField(max_length=100, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    menu_level = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'menus'
        managed = False
        ordering = ['display_order', 'id']

    def __str__(self):
        return name_with_code(self.menu_name, self.menu_code)


class MenuPermission(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, db_column='menu_id')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column='permission_id')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'menu_permissions'
        managed = False


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column='permission_id')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'role_permissions'
        managed = False
