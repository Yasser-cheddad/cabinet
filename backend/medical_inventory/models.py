from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from accounts.models import User

class InventoryCategory(models.Model):
    """Model for categorizing inventory items"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Category Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    
    # For hierarchical categories
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Parent Category')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Inventory Category')
        verbose_name_plural = _('Inventory Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Model for medical inventory items"""
    STATUS_CHOICES = [
        ('in_stock', _('In Stock')),
        ('low_stock', _('Low Stock')),
        ('out_of_stock', _('Out of Stock')),
        ('discontinued', _('Discontinued')),
        ('on_order', _('On Order')),
    ]
    
    name = models.CharField(max_length=255, verbose_name=_('Item Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items',
        verbose_name=_('Category')
    )
    
    # Identification
    sku = models.CharField(max_length=50, unique=True, verbose_name=_('SKU'))
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Barcode'))
    
    # Stock information
    quantity = models.PositiveIntegerField(default=0, verbose_name=_('Current Quantity'))
    unit = models.CharField(max_length=50, default='unit', verbose_name=_('Unit'))
    minimum_stock = models.PositiveIntegerField(default=5, verbose_name=_('Minimum Stock Level'))
    maximum_stock = models.PositiveIntegerField(default=100, verbose_name=_('Maximum Stock Level'))
    
    # Pricing
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Purchase Price')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_stock',
        verbose_name=_('Status')
    )
    
    # Dates
    expiry_date = models.DateField(blank=True, null=True, verbose_name=_('Expiry Date'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Location
    storage_location = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Storage Location'))
    
    class Meta:
        verbose_name = _('Inventory Item')
        verbose_name_plural = _('Inventory Items')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def update_status(self):
        """Update the status based on current quantity"""
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity < self.minimum_stock:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
        self.save(update_fields=['status'])
        return self.status

class InventoryTransaction(models.Model):
    """Model for tracking inventory movements"""
    TRANSACTION_TYPES = [
        ('purchase', _('Purchase')),
        ('usage', _('Usage')),
        ('adjustment', _('Adjustment')),
        ('return', _('Return')),
        ('transfer', _('Transfer')),
        ('expired', _('Expired')),
    ]
    
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Item')
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name=_('Transaction Type')
    )
    
    quantity = models.IntegerField(verbose_name=_('Quantity'))
    
    # Quantity before and after for audit purposes
    quantity_before = models.PositiveIntegerField(verbose_name=_('Quantity Before'))
    quantity_after = models.PositiveIntegerField(verbose_name=_('Quantity After'))
    
    # Who performed the transaction
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_transactions',
        verbose_name=_('Performed By')
    )
    
    # Reference to related objects (e.g., purchase order, prescription)
    reference_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Reference ID'))
    reference_type = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Reference Type'))
    
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Inventory Transaction')
        verbose_name_plural = _('Inventory Transactions')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.transaction_type}: {self.item.name} ({self.quantity})"

class Supplier(models.Model):
    """Model for inventory suppliers"""
    name = models.CharField(max_length=255, verbose_name=_('Supplier Name'))
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Contact Person'))
    email = models.EmailField(blank=True, null=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Phone'))
    address = models.TextField(blank=True, null=True, verbose_name=_('Address'))
    website = models.URLField(blank=True, null=True, verbose_name=_('Website'))
    
    # Status and rating
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    rating = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Rating (0-5)'))
    
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    """Model for purchase orders"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('ordered', _('Ordered')),
        ('partially_received', _('Partially Received')),
        ('received', _('Received')),
        ('cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name=_('Order Number'))
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        verbose_name=_('Supplier')
    )
    
    # Dates
    order_date = models.DateField(verbose_name=_('Order Date'))
    expected_delivery_date = models.DateField(blank=True, null=True, verbose_name=_('Expected Delivery Date'))
    delivery_date = models.DateField(blank=True, null=True, verbose_name=_('Actual Delivery Date'))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    # Who created and approved
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchase_orders',
        verbose_name=_('Created By')
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        verbose_name=_('Approved By')
    )
    
    # Financial information
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name=_('Total Amount')
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name=_('Shipping Cost')
    )
    
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name=_('Tax Amount')
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Purchase Order')
        verbose_name_plural = _('Purchase Orders')
        ordering = ['-order_date']
    
    def __str__(self):
        return f"PO-{self.order_number} ({self.supplier.name})"
    
    @property
    def grand_total(self):
        """Calculate the grand total including shipping and tax"""
        return self.total_amount + self.shipping_cost + self.tax_amount

class PurchaseOrderItem(models.Model):
    """Model for items in a purchase order"""
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Purchase Order')
    )
    
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='purchase_order_items',
        verbose_name=_('Item')
    )
    
    quantity_ordered = models.PositiveIntegerField(verbose_name=_('Quantity Ordered'))
    quantity_received = models.PositiveIntegerField(default=0, verbose_name=_('Quantity Received'))
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Unit Price')
    )
    
    # Status tracking
    is_fully_received = models.BooleanField(default=False, verbose_name=_('Fully Received'))
    
    class Meta:
        verbose_name = _('Purchase Order Item')
        verbose_name_plural = _('Purchase Order Items')
        unique_together = ['purchase_order', 'item']
    
    def __str__(self):
        return f"{self.item.name} - {self.quantity_ordered} {self.item.unit}"
    
    @property
    def subtotal(self):
        """Calculate the subtotal for this item"""
        return self.quantity_ordered * self.unit_price
    
    def update_received_status(self):
        """Update the fully received status based on quantities"""
        self.is_fully_received = self.quantity_received >= self.quantity_ordered
        self.save(update_fields=['is_fully_received'])
        return self.is_fully_received
