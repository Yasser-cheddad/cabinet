from rest_framework import serializers
from .models import (
    InventoryCategory, InventoryItem, InventoryTransaction,
    Supplier, PurchaseOrder, PurchaseOrderItem
)

class InventoryCategorySerializer(serializers.ModelSerializer):
    """Serializer for inventory categories"""
    parent_name = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryCategory
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'created_at', 'updated_at', 'item_count'
        ]
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None
    
    def get_item_count(self, obj):
        return obj.items.count()

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for inventory items"""
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'description', 'sku', 'barcode', 'category', 
            'category_name', 'quantity', 'unit', 'minimum_stock', 
            'maximum_stock', 'purchase_price', 'status', 'expiry_date', 
            'storage_location', 'created_at', 'updated_at'
        ]
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

class InventoryTransactionSerializer(serializers.ModelSerializer):
    """Serializer for inventory transactions"""
    item_name = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'item', 'item_name', 'transaction_type', 'quantity',
            'quantity_before', 'quantity_after', 'performed_by', 
            'performed_by_name', 'timestamp', 'reference_id', 
            'reference_type', 'notes'
        ]
    
    def get_item_name(self, obj):
        return obj.item.name
    
    def get_performed_by_name(self, obj):
        return obj.performed_by.get_full_name() if obj.performed_by else None

class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for suppliers"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_name', 'email', 'phone', 'address',
            'website', 'notes', 'is_active', 'rating', 'created_at', 
            'updated_at'
        ]

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for purchase order items"""
    item_name = serializers.SerializerMethodField()
    item_sku = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'item', 'item_name', 'item_sku',
            'quantity', 'unit_price', 'total_price', 'received_quantity',
            'is_received'
        ]
    
    def get_item_name(self, obj):
        return obj.item.name
    
    def get_item_sku(self, obj):
        return obj.item.sku

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders"""
    supplier_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'reference_number', 'supplier', 
            'supplier_name', 'status', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'expected_delivery_date', 
            'delivery_date', 'shipping_cost', 'tax_amount', 
            'discount_amount', 'total_amount', 'payment_status', 
            'payment_date', 'notes', 'items'
        ]
    
    def get_supplier_name(self, obj):
        return obj.supplier.name
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
