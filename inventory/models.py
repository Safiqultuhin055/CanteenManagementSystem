from django.db import models

from core.model_display import name_with_code

class FoodCategory(models.Model):
    category_name = models.CharField(max_length=150, unique=True)
    category_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'food_categories'
        managed = False

    def __str__(self):
        return name_with_code(self.category_name, self.category_code)

class MenuItem(models.Model):
    category = models.ForeignKey(FoodCategory, on_delete=models.PROTECT, db_column='category_id')
    item_name = models.CharField(max_length=200, unique=True)
    item_name_bn = models.CharField('Name (Bangla)', max_length=200, blank=True, null=True)
    item_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_vegetarian = models.BooleanField(default=False)
    image_path = models.CharField(max_length=500, blank=True, null=True)
    image_data = models.BinaryField(blank=True, null=True, db_column='image_data')
    image_content_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'menu_items'
        managed = False

    def __str__(self):
        return name_with_code(self.item_name, self.item_code)

    @property
    def has_image(self):
        if hasattr(self, '_has_image'):
            return bool(self._has_image)
        from inventory.services.menu_image_cache import item_has_image
        return item_has_image(self.pk)

    def get_image_url(self):
        if not self.has_image:
            return None
        from django.urls import reverse
        url = reverse('inventory:menu_item_image', args=[self.pk])
        # Cache-buster: token changes when the row's updated_at changes, so a
        # re-uploaded image is fetched fresh despite the immutable Cache-Control.
        version = getattr(self, 'updated_at', None)
        if version:
            import hashlib
            token = hashlib.md5(str(version).encode(), usedforsecurity=False).hexdigest()[:12]
            url = f'{url}?v={token}'
        return url

class Supplier(models.Model):
    supplier_name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'suppliers'
        managed = False

    def __str__(self):
        return self.supplier_name

class RawMaterial(models.Model):
    material_name = models.CharField(max_length=200, unique=True)
    material_code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    unit_of_measure = models.CharField(max_length=20)
    minimum_stock_level = models.DecimalField(max_digits=18, decimal_places=3, default=0)
    default_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, db_column='default_supplier_id')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'raw_materials'
        managed = False

    def __str__(self):
        return name_with_code(self.material_name, self.material_code)

class RawMaterialStock(models.Model):
    raw_material = models.OneToOneField(RawMaterial, on_delete=models.CASCADE, db_column='raw_material_id')
    current_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=0)
    last_purchase_price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    average_price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'raw_material_stock'
        managed = False

    def __str__(self):
        return f"{self.raw_material.material_name} - {self.current_quantity}"

class DailyFoodStock(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, db_column='menu_item_id')
    stock_date = models.DateField()
    expired_date = models.DateField('Expired date', null=True, blank=True)
    prepared_quantity = models.IntegerField(default=0)
    sold_quantity = models.IntegerField(default=0)
    waste_quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    preparation_time = models.DateTimeField(null=True, blank=True)
    ready_time = models.DateTimeField(null=True, blank=True)
    prepared_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='prepared_by',
        related_name='prepared_daily_stocks',
    )
    remarks = models.CharField(max_length=300, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'daily_food_stock'
        managed = False

    def __str__(self):
        return f"{self.menu_item.item_name} on {self.stock_date}"


class WasteRecord(models.Model):
    WASTE_TYPE_FOOD = 'FOOD'
    WASTE_TYPE_RAW = 'RAW_MATERIAL'
    WASTE_TYPE_CHOICES = [
        (WASTE_TYPE_FOOD, 'Food'),
        (WASTE_TYPE_RAW, 'Raw material'),
    ]
    WASTE_REASON_CHOICES = [
        ('EXPIRED', 'Expired'),
        ('SPOILED', 'Spoiled'),
        ('OVERPRODUCTION', 'Overproduction'),
        ('QUALITY_ISSUE', 'Quality issue'),
        ('OTHER', 'Other'),
    ]

    waste_date = models.DateField()
    waste_type = models.CharField(
        max_length=50, choices=WASTE_TYPE_CHOICES, default=WASTE_TYPE_FOOD,
    )
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.SET_NULL, null=True, blank=True, db_column='menu_item_id',
    )
    raw_material = models.ForeignKey(
        RawMaterial, on_delete=models.SET_NULL, null=True, blank=True, db_column='raw_material_id',
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=3)
    unit_of_measure = models.CharField(max_length=50)
    estimated_cost = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    waste_reason = models.CharField(max_length=100, choices=WASTE_REASON_CHOICES, default='OTHER')
    remarks = models.CharField(max_length=500, null=True, blank=True)
    reported_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='reported_by',
        related_name='waste_records_reported',
    )
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='verified_by',
        related_name='waste_records_verified',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'waste_records'
        managed = False

    def __str__(self):
        return f"{self.waste_type} - {self.waste_date}"
