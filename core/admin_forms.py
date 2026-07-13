"""Custom ModelForms for all Django admin modules."""
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import models

from core.admin_base import FORM_CHECK, FORM_CONTROL, FORM_NUMBER, FORM_SELECT, FORM_TEXTAREA
from core.business_date import get_business_date

DATETIME_LOCAL_FORMATS = [
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
]


class DateTimeLocalField(forms.DateTimeField):
    """Accept HTML5 datetime-local values from admin inputs."""

    input_formats = DATETIME_LOCAL_FORMATS

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            forms.DateTimeInput(
                attrs={**FORM_CONTROL, 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        )
        super().__init__(*args, **kwargs)


class CanteenAdminModelForm(forms.ModelForm):
    """Use DateTimeLocalField for model DateTimeFields (datetime-local widgets)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in list(self.fields.items()):
            try:
                model_field = self._meta.model._meta.get_field(name)
            except Exception:
                continue
            if isinstance(model_field, models.DateTimeField):
                self.fields[name] = DateTimeLocalField(
                    required=field.required,
                    label=field.label,
                    help_text=field.help_text,
                    initial=field.initial,
                )


def _widgets_for_model(model, extra=None):
    w = {}
    for field in model._meta.fields:
        if isinstance(field, models.BooleanField):
            w[field.name] = forms.CheckboxInput(attrs=FORM_CHECK)
        elif isinstance(field, (models.ForeignKey, models.OneToOneField)):
            # Leave FK widgets unset so ModelAdmin autocomplete_fields apply.
            continue
        elif isinstance(field, models.TextField):
            w[field.name] = forms.Textarea(attrs=FORM_TEXTAREA)
        elif isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
            w[field.name] = forms.NumberInput(attrs=FORM_NUMBER)
        elif isinstance(field, models.ImageField):
            w[field.name] = forms.ClearableFileInput(attrs={**FORM_CONTROL, 'accept': 'image/*'})
        elif isinstance(field, models.FileField):
            w[field.name] = forms.ClearableFileInput(attrs=FORM_CONTROL)
        elif isinstance(field, models.DateField):
            w[field.name] = forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'})
        elif isinstance(field, models.DateTimeField):
            w[field.name] = forms.DateTimeInput(
                attrs={**FORM_CONTROL, 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            )
        else:
            w[field.name] = forms.TextInput(attrs=FORM_CONTROL)
    if extra:
        w.update(extra)
    return w


from users.models import Menu, MenuPermission, Permission, Role, RolePermission, User, UserRole
from employee.models import Department, Employee, EmployeeCard
from inventory.models import (
    DailyFoodStock, FoodCategory, MenuItem, RawMaterial,
    RawMaterialStock, Supplier, WasteRecord,
)
from balance.models import (
    BalanceAllocation, CardTransaction, CreditLimit,
    EmployeeBalance, MonthlyAllowance,
)
from pos.models import GuestCard, Order, OrderDetail, Payment
from core.models import ApiIntegration, AuditLog, SystemSetting


_COMMON_EXCLUDE = ('is_deleted', 'created_at', 'updated_at', 'created_by', 'updated_by')


class RoleAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Role
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Role)


class PermissionAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Permission
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Permission)


class MenuAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Menu
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Menu)


class MenuPermissionAdminForm(CanteenAdminModelForm):
    class Meta:
        model = MenuPermission
        fields = '__all__'
        widgets = _widgets_for_model(MenuPermission)


class RolePermissionAdminForm(CanteenAdminModelForm):
    class Meta:
        model = RolePermission
        fields = '__all__'
        exclude = ('is_deleted',)
        widgets = _widgets_for_model(RolePermission)


class UserRoleAdminForm(CanteenAdminModelForm):
    class Meta:
        model = UserRole
        fields = '__all__'
        exclude = ('is_deleted', 'created_at', 'updated_at', 'created_by', 'updated_by')
        widgets = _widgets_for_model(UserRole)


class CanteenUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'
        widgets = _widgets_for_model(User, {
            'password': forms.PasswordInput(attrs=FORM_CONTROL, render_value=True),
        })


class CanteenUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'is_staff', 'is_active')
        widgets = _widgets_for_model(User)


class DepartmentAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Department)


class EmployeeAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Employee)


class EmployeeCardAdminForm(CanteenAdminModelForm):
    class Meta:
        model = EmployeeCard
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(EmployeeCard)


class FoodCategoryAdminForm(CanteenAdminModelForm):
    class Meta:
        model = FoodCategory
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(FoodCategory)


class MenuItemAdminForm(CanteenAdminModelForm):
    image_upload = forms.ImageField(
        required=False,
        label='Upload image',
        help_text='Saved in SQL Server (image_data BLOB), not as a media file.',
    )

    class Meta:
        model = MenuItem
        fields = '__all__'
        exclude = _COMMON_EXCLUDE + ('image_data', 'image_content_type', 'image_path')
        widgets = _widgets_for_model(MenuItem)


class SupplierAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Supplier)


class RawMaterialAdminForm(CanteenAdminModelForm):
    class Meta:
        model = RawMaterial
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(RawMaterial)


class RawMaterialStockAdminForm(CanteenAdminModelForm):
    class Meta:
        model = RawMaterialStock
        fields = '__all__'
        widgets = _widgets_for_model(RawMaterialStock)


class DailyFoodStockAdminForm(CanteenAdminModelForm):
    class Meta:
        model = DailyFoodStock
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(DailyFoodStock)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and 'stock_date' in self.fields:
            self.fields['stock_date'].initial = get_business_date()

    def clean(self):
        cleaned = super().clean()
        menu_item = cleaned.get('menu_item')
        stock_date = cleaned.get('stock_date')
        if menu_item and stock_date:
            qs = DailyFoodStock.objects.filter(
                menu_item=menu_item,
                stock_date=stock_date,
                is_deleted=False,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    'Daily stock for this menu item on this date already exists.'
                )
        return cleaned


class WasteRecordAdminForm(CanteenAdminModelForm):
    class Meta:
        model = WasteRecord
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(WasteRecord)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and 'waste_date' in self.fields:
            self.fields['waste_date'].initial = get_business_date()


class EmployeeBalanceAdminForm(CanteenAdminModelForm):
    class Meta:
        model = EmployeeBalance
        fields = '__all__'
        widgets = _widgets_for_model(EmployeeBalance)


class BalanceAllocationAdminForm(CanteenAdminModelForm):
    class Meta:
        model = BalanceAllocation
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(BalanceAllocation)


class MonthlyAllowanceAdminForm(CanteenAdminModelForm):
    class Meta:
        model = MonthlyAllowance
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(MonthlyAllowance)


class CreditLimitAdminForm(CanteenAdminModelForm):
    class Meta:
        model = CreditLimit
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(CreditLimit)


class CardTransactionAdminForm(CanteenAdminModelForm):
    class Meta:
        model = CardTransaction
        fields = '__all__'
        exclude = ('is_deleted', 'created_at')
        widgets = _widgets_for_model(CardTransaction)


class OrderAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(Order)


class OrderDetailAdminForm(CanteenAdminModelForm):
    class Meta:
        model = OrderDetail
        fields = '__all__'
        exclude = ('is_deleted', 'created_at')
        widgets = _widgets_for_model(OrderDetail)


class PaymentAdminForm(CanteenAdminModelForm):
    class Meta:
        model = Payment
        fields = '__all__'
        exclude = ('is_deleted', 'created_at')
        widgets = _widgets_for_model(Payment)


class GuestCardAdminForm(CanteenAdminModelForm):
    class Meta:
        model = GuestCard
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(GuestCard)


class SystemSettingAdminForm(CanteenAdminModelForm):
    class Meta:
        model = SystemSetting
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(SystemSetting)


class AuditLogAdminForm(CanteenAdminModelForm):
    class Meta:
        model = AuditLog
        fields = '__all__'
        widgets = _widgets_for_model(AuditLog)


class ApiIntegrationAdminForm(CanteenAdminModelForm):
    class Meta:
        model = ApiIntegration
        fields = '__all__'
        exclude = _COMMON_EXCLUDE
        widgets = _widgets_for_model(ApiIntegration, extra={
            'provider': forms.Select(attrs=FORM_SELECT, choices=ApiIntegration.PROVIDER_CHOICES),
            'api_key': forms.PasswordInput(attrs={**FORM_CONTROL, 'autocomplete': 'new-password'},
                                           render_value=True),
        })
        help_texts = {
            'is_default': 'Preferred row when a provider has more than one key.',
            'extra_config': 'Optional JSON for extra parameters.',
        }
