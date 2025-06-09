from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Sum, F, Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    InventoryCategory, InventoryItem, InventoryTransaction,
    Supplier, PurchaseOrder, PurchaseOrderItem
)

# Custom permission classes
class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow read access to all users, but write access only to staff"""
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to staff users
        return request.user and request.user.is_staff

# Inventory Category Views
@api_view(['GET'])
def get_inventory_categories(request):
    """Get all inventory categories"""
    categories = InventoryCategory.objects.all()
    
    # Format response data
    data = [{
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent.id if category.parent else None,
        'item_count': category.items.count()
    } for category in categories]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_category_detail(request, category_id):
    """Get details of a specific category"""
    category = get_object_or_404(InventoryCategory, id=category_id)
    
    # Get subcategories
    subcategories = category.subcategories.all()
    
    # Get items in this category
    items = category.items.all()
    
    data = {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent.id if category.parent else None,
        'created_at': category.created_at,
        'updated_at': category.updated_at,
        'subcategories': [{
            'id': subcat.id,
            'name': subcat.name,
            'item_count': subcat.items.count()
        } for subcat in subcategories],
        'items': [{
            'id': item.id,
            'name': item.name,
            'sku': item.sku,
            'quantity': item.quantity,
            'status': item.status
        } for item in items]
    }
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def create_category(request):
    """Create a new inventory category"""
    name = request.data.get('name')
    description = request.data.get('description', '')
    parent_id = request.data.get('parent_id')
    
    # Validate required fields
    if not name:
        return Response({
            'error': _('Category name is required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if category with this name already exists
    if InventoryCategory.objects.filter(name=name).exists():
        return Response({
            'error': _('A category with this name already exists')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get parent category if provided
    parent = None
    if parent_id:
        try:
            parent = InventoryCategory.objects.get(id=parent_id)
        except InventoryCategory.DoesNotExist:
            return Response({
                'error': _('Parent category not found')
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the category
    category = InventoryCategory.objects.create(
        name=name,
        description=description,
        parent=parent
    )
    
    return Response({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent.id if category.parent else None,
        'created_at': category.created_at
    }, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def update_category(request, category_id):
    """Update an existing inventory category"""
    category = get_object_or_404(InventoryCategory, id=category_id)
    
    # Update fields if provided
    if 'name' in request.data:
        # Check if another category with this name exists
        if InventoryCategory.objects.filter(name=request.data['name']).exclude(id=category_id).exists():
            return Response({
                'error': _('A category with this name already exists')
            }, status=status.HTTP_400_BAD_REQUEST)
        category.name = request.data['name']
    
    if 'description' in request.data:
        category.description = request.data['description']
    
    if 'parent_id' in request.data:
        parent_id = request.data['parent_id']
        if parent_id:
            # Ensure we're not creating a circular reference
            if parent_id == category.id:
                return Response({
                    'error': _('A category cannot be its own parent')
                }, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                parent = InventoryCategory.objects.get(id=parent_id)
                category.parent = parent
            except InventoryCategory.DoesNotExist:
                return Response({
                    'error': _('Parent category not found')
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            category.parent = None
    
    # Save changes
    category.save()
    
    return Response({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent.id if category.parent else None,
        'updated_at': category.updated_at
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def delete_category(request, category_id):
    """Delete an inventory category"""
    category = get_object_or_404(InventoryCategory, id=category_id)
    
    # Check if category has items
    if category.items.exists():
        return Response({
            'error': _('Cannot delete category with items. Move or delete the items first.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if category has subcategories
    if category.subcategories.exists():
        return Response({
            'error': _('Cannot delete category with subcategories. Move or delete the subcategories first.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Delete the category
    category.delete()
    
    return Response({
        'success': _('Category deleted successfully')
    }, status=status.HTTP_200_OK)

# Inventory Item Views
@api_view(['GET'])
def get_inventory_items(request):
    """Get all inventory items with optional filtering"""
    # Get query parameters
    category_id = request.query_params.get('category_id')
    status_filter = request.query_params.get('status')
    search_query = request.query_params.get('search')
    low_stock_only = request.query_params.get('low_stock') == 'true'
    
    # Base query
    queryset = InventoryItem.objects.all()
    
    # Apply filters
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if low_stock_only:
        queryset = queryset.filter(quantity__lt=F('minimum_stock'))
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) | 
            Q(barcode__icontains=search_query)
        )
    
    # Format response data
    data = [{
        'id': item.id,
        'name': item.name,
        'sku': item.sku,
        'category': {
            'id': item.category.id,
            'name': item.category.name
        } if item.category else None,
        'quantity': item.quantity,
        'unit': item.unit,
        'status': item.status,
        'purchase_price': str(item.purchase_price),
        'expiry_date': item.expiry_date,
        'storage_location': item.storage_location
    } for item in queryset]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_item_detail(request, item_id):
    """Get details of a specific inventory item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    # Get recent transactions for this item
    transactions = item.transactions.order_by('-timestamp')[:10]
    
    data = {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'sku': item.sku,
        'barcode': item.barcode,
        'category': {
            'id': item.category.id,
            'name': item.category.name
        } if item.category else None,
        'quantity': item.quantity,
        'unit': item.unit,
        'minimum_stock': item.minimum_stock,
        'maximum_stock': item.maximum_stock,
        'purchase_price': str(item.purchase_price),
        'status': item.status,
        'expiry_date': item.expiry_date,
        'storage_location': item.storage_location,
        'created_at': item.created_at,
        'updated_at': item.updated_at,
        'recent_transactions': [{
            'id': transaction.id,
            'transaction_type': transaction.transaction_type,
            'quantity': transaction.quantity,
            'timestamp': transaction.timestamp,
            'performed_by': transaction.performed_by.get_full_name() if transaction.performed_by else None
        } for transaction in transactions]
    }
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def create_item(request):
    """Create a new inventory item"""
    # Get data from request
    name = request.data.get('name')
    description = request.data.get('description', '')
    category_id = request.data.get('category_id')
    sku = request.data.get('sku')
    barcode = request.data.get('barcode')
    quantity = request.data.get('quantity', 0)
    unit = request.data.get('unit', 'unit')
    minimum_stock = request.data.get('minimum_stock', 5)
    maximum_stock = request.data.get('maximum_stock', 100)
    purchase_price = request.data.get('purchase_price')
    expiry_date = request.data.get('expiry_date')
    storage_location = request.data.get('storage_location', '')
    
    # Validate required fields
    if not all([name, sku, purchase_price]):
        return Response({
            'error': _('Name, SKU, and purchase price are required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if item with this SKU already exists
    if InventoryItem.objects.filter(sku=sku).exists():
        return Response({
            'error': _('An item with this SKU already exists')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get category if provided
    category = None
    if category_id:
        try:
            category = InventoryCategory.objects.get(id=category_id)
        except InventoryCategory.DoesNotExist:
            return Response({
                'error': _('Category not found')
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the item
    try:
        item = InventoryItem.objects.create(
            name=name,
            description=description,
            category=category,
            sku=sku,
            barcode=barcode,
            quantity=int(quantity),
            unit=unit,
            minimum_stock=int(minimum_stock),
            maximum_stock=int(maximum_stock),
            purchase_price=purchase_price,
            expiry_date=expiry_date,
            storage_location=storage_location
        )
        
        # Update status based on quantity
        item.update_status()
        
        # Create initial inventory transaction if quantity > 0
        if int(quantity) > 0:
            InventoryTransaction.objects.create(
                item=item,
                transaction_type='adjustment',
                quantity=int(quantity),
                quantity_before=0,
                quantity_after=int(quantity),
                performed_by=request.user,
                notes=_('Initial inventory')
            )
        
        return Response({
            'id': item.id,
            'name': item.name,
            'sku': item.sku,
            'category': {
                'id': item.category.id,
                'name': item.category.name
            } if item.category else None,
            'quantity': item.quantity,
            'status': item.status,
            'created_at': item.created_at
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def update_item(request, item_id):
    """Update an existing inventory item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    # Update fields if provided
    if 'name' in request.data:
        item.name = request.data['name']
    
    if 'description' in request.data:
        item.description = request.data['description']
    
    if 'category_id' in request.data:
        category_id = request.data['category_id']
        if category_id:
            try:
                category = InventoryCategory.objects.get(id=category_id)
                item.category = category
            except InventoryCategory.DoesNotExist:
                return Response({
                    'error': _('Category not found')
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            item.category = None
    
    if 'sku' in request.data:
        # Check if another item with this SKU exists
        if InventoryItem.objects.filter(sku=request.data['sku']).exclude(id=item_id).exists():
            return Response({
                'error': _('An item with this SKU already exists')
            }, status=status.HTTP_400_BAD_REQUEST)
        item.sku = request.data['sku']
    
    if 'barcode' in request.data:
        item.barcode = request.data['barcode']
    
    if 'minimum_stock' in request.data:
        item.minimum_stock = int(request.data['minimum_stock'])
    
    if 'maximum_stock' in request.data:
        item.maximum_stock = int(request.data['maximum_stock'])
    
    if 'purchase_price' in request.data:
        item.purchase_price = request.data['purchase_price']
    
    if 'unit' in request.data:
        item.unit = request.data['unit']
    
    if 'expiry_date' in request.data:
        item.expiry_date = request.data['expiry_date']
    
    if 'storage_location' in request.data:
        item.storage_location = request.data['storage_location']
    
    # Save changes
    item.save()
    
    # Update status based on quantity
    item.update_status()
    
    return Response({
        'id': item.id,
        'name': item.name,
        'sku': item.sku,
        'category': {
            'id': item.category.id,
            'name': item.category.name
        } if item.category else None,
        'quantity': item.quantity,
        'status': item.status,
        'updated_at': item.updated_at
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def adjust_inventory(request, item_id):
    """Adjust inventory quantity for an item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    # Get data from request
    quantity = request.data.get('quantity')
    transaction_type = request.data.get('transaction_type', 'adjustment')
    notes = request.data.get('notes', '')
    
    # Validate quantity
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return Response({
            'error': _('Quantity must be a valid integer')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate transaction type
    valid_types = ['purchase', 'usage', 'adjustment', 'return', 'transfer', 'expired']
    if transaction_type not in valid_types:
        return Response({
            'error': _('Invalid transaction type')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # For usage, return, and expired, quantity should be negative
    if transaction_type in ['usage', 'expired'] and quantity > 0:
        quantity = -quantity
    
    # Check if we have enough stock for negative adjustments
    if quantity < 0 and abs(quantity) > item.quantity:
        return Response({
            'error': _('Not enough stock for this adjustment')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the transaction
    try:
        # Record quantity before
        quantity_before = item.quantity
        
        # Update item quantity
        item.quantity += quantity
        item.save()
        
        # Update status
        item.update_status()
        
        # Create transaction record
        transaction = InventoryTransaction.objects.create(
            item=item,
            transaction_type=transaction_type,
            quantity=quantity,
            quantity_before=quantity_before,
            quantity_after=item.quantity,
            performed_by=request.user,
            notes=notes
        )
        
        return Response({
            'success': _('Inventory adjusted successfully'),
            'item': {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'status': item.status
            },
            'transaction': {
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'quantity': transaction.quantity,
                'timestamp': transaction.timestamp
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def delete_item(request, item_id):
    """Delete an inventory item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    # Check if item has transactions
    if item.transactions.exists():
        return Response({
            'error': _('Cannot delete item with transaction history. Consider marking it as discontinued instead.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if item is in any purchase orders
    if item.purchase_order_items.exists():
        return Response({
            'error': _('Cannot delete item that is part of purchase orders.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Delete the item
    item.delete()
    
    return Response({
        'success': _('Item deleted successfully')
    }, status=status.HTTP_200_OK)

# Supplier Views
@api_view(['GET'])
def get_suppliers(request):
    """Get all suppliers with optional filtering"""
    # Get query parameters
    search_query = request.query_params.get('search')
    active_only = request.query_params.get('active_only') == 'true'
    
    # Base query
    queryset = Supplier.objects.all()
    
    # Apply filters
    if active_only:
        queryset = queryset.filter(is_active=True)
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(contact_name__icontains=search_query) | 
            Q(email__icontains=search_query) | 
            Q(phone__icontains=search_query)
        )
    
    # Format response data
    data = [{
        'id': supplier.id,
        'name': supplier.name,
        'contact_name': supplier.contact_name,
        'email': supplier.email,
        'phone': supplier.phone,
        'is_active': supplier.is_active,
        'rating': supplier.rating
    } for supplier in queryset]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_supplier_detail(request, supplier_id):
    """Get details of a specific supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    # Get recent purchase orders for this supplier
    purchase_orders = supplier.purchase_orders.order_by('-created_at')[:5]
    
    data = {
        'id': supplier.id,
        'name': supplier.name,
        'contact_name': supplier.contact_name,
        'email': supplier.email,
        'phone': supplier.phone,
        'address': supplier.address,
        'website': supplier.website,
        'notes': supplier.notes,
        'is_active': supplier.is_active,
        'rating': supplier.rating,
        'created_at': supplier.created_at,
        'updated_at': supplier.updated_at,
        'recent_purchase_orders': [{
            'id': po.id,
            'order_number': po.order_number,
            'status': po.status,
            'total_amount': str(po.total_amount),
            'created_at': po.created_at
        } for po in purchase_orders]
    }
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def create_supplier(request):
    """Create a new supplier"""
    # Get data from request
    name = request.data.get('name')
    contact_name = request.data.get('contact_name', '')
    email = request.data.get('email', '')
    phone = request.data.get('phone', '')
    address = request.data.get('address', '')
    website = request.data.get('website', '')
    notes = request.data.get('notes', '')
    is_active = request.data.get('is_active', True)
    
    # Validate required fields
    if not name:
        return Response({
            'error': _('Supplier name is required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the supplier
    try:
        supplier = Supplier.objects.create(
            name=name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            address=address,
            website=website,
            notes=notes,
            is_active=is_active
        )
        
        return Response({
            'id': supplier.id,
            'name': supplier.name,
            'contact_name': supplier.contact_name,
            'email': supplier.email,
            'phone': supplier.phone,
            'is_active': supplier.is_active,
            'created_at': supplier.created_at
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def update_supplier(request, supplier_id):
    """Update an existing supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    # Update fields if provided
    if 'name' in request.data:
        supplier.name = request.data['name']
    
    if 'contact_name' in request.data:
        supplier.contact_name = request.data['contact_name']
    
    if 'email' in request.data:
        supplier.email = request.data['email']
    
    if 'phone' in request.data:
        supplier.phone = request.data['phone']
    
    if 'address' in request.data:
        supplier.address = request.data['address']
    
    if 'website' in request.data:
        supplier.website = request.data['website']
    
    if 'notes' in request.data:
        supplier.notes = request.data['notes']
    
    if 'is_active' in request.data:
        supplier.is_active = request.data['is_active']
    
    if 'rating' in request.data:
        try:
            rating = int(request.data['rating'])
            if 1 <= rating <= 5:
                supplier.rating = rating
            else:
                return Response({
                    'error': _('Rating must be between 1 and 5')
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': _('Rating must be a valid integer')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Save changes
    supplier.save()
    
    return Response({
        'id': supplier.id,
        'name': supplier.name,
        'contact_name': supplier.contact_name,
        'email': supplier.email,
        'phone': supplier.phone,
        'is_active': supplier.is_active,
        'rating': supplier.rating,
        'updated_at': supplier.updated_at
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def delete_supplier(request, supplier_id):
    """Delete a supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    # Check if supplier has purchase orders
    if supplier.purchase_orders.exists():
        return Response({
            'error': _('Cannot delete supplier with purchase orders. Consider marking it as inactive instead.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Delete the supplier
    supplier.delete()
    
    return Response({
        'success': _('Supplier deleted successfully')
    }, status=status.HTTP_200_OK)

# Purchase Order Views
@api_view(['GET'])
def get_purchase_orders(request):
    """Get all purchase orders with optional filtering"""
    # Get query parameters
    supplier_id = request.query_params.get('supplier_id')
    status_filter = request.query_params.get('status')
    search_query = request.query_params.get('search')
    
    # Base query
    queryset = PurchaseOrder.objects.all()
    
    # Apply filters
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if search_query:
        queryset = queryset.filter(
            Q(order_number__icontains=search_query) | 
            Q(reference_number__icontains=search_query) | 
            Q(notes__icontains=search_query)
        )
    
    # Format response data
    data = [{
        'id': po.id,
        'order_number': po.order_number,
        'supplier': {
            'id': po.supplier.id,
            'name': po.supplier.name
        },
        'status': po.status,
        'total_amount': str(po.total_amount),
        'created_at': po.created_at,
        'expected_delivery_date': po.expected_delivery_date
    } for po in queryset]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_purchase_order_detail(request, po_id):
    """Get details of a specific purchase order"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Get items in this purchase order
    items = po.items.all()
    
    data = {
        'id': po.id,
        'order_number': po.order_number,
        'reference_number': po.reference_number,
        'supplier': {
            'id': po.supplier.id,
            'name': po.supplier.name,
            'contact_name': po.supplier.contact_name,
            'email': po.supplier.email,
            'phone': po.supplier.phone
        },
        'status': po.status,
        'created_by': po.created_by.get_full_name() if po.created_by else None,
        'created_at': po.created_at,
        'updated_at': po.updated_at,
        'expected_delivery_date': po.expected_delivery_date,
        'delivery_date': po.delivery_date,
        'shipping_cost': str(po.shipping_cost),
        'tax_amount': str(po.tax_amount),
        'discount_amount': str(po.discount_amount),
        'total_amount': str(po.total_amount),
        'payment_status': po.payment_status,
        'payment_date': po.payment_date,
        'notes': po.notes,
        'items': [{
            'id': item.id,
            'item': {
                'id': item.item.id,
                'name': item.item.name,
                'sku': item.item.sku
            },
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'total_price': str(item.total_price),
            'received_quantity': item.received_quantity,
            'is_received': item.is_received
        } for item in items]
    }
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def create_purchase_order(request):
    """Create a new purchase order"""
    # Get data from request
    supplier_id = request.data.get('supplier_id')
    reference_number = request.data.get('reference_number', '')
    expected_delivery_date = request.data.get('expected_delivery_date')
    shipping_cost = request.data.get('shipping_cost', 0)
    tax_amount = request.data.get('tax_amount', 0)
    discount_amount = request.data.get('discount_amount', 0)
    notes = request.data.get('notes', '')
    items_data = request.data.get('items', [])
    
    # Validate required fields
    if not supplier_id:
        return Response({
            'error': _('Supplier is required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not items_data:
        return Response({
            'error': _('At least one item is required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get supplier
    try:
        supplier = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        return Response({
            'error': _('Supplier not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the purchase order
    try:
        # Generate order number
        today = timezone.now().date()
        order_count = PurchaseOrder.objects.filter(
            created_at__date=today
        ).count() + 1
        order_number = f"PO-{today.strftime('%Y%m%d')}-{order_count:03d}"
        
        # Create purchase order
        po = PurchaseOrder.objects.create(
            order_number=order_number,
            reference_number=reference_number,
            supplier=supplier,
            expected_delivery_date=expected_delivery_date,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            notes=notes,
            created_by=request.user,
            status='draft'
        )
        
        # Add items to purchase order
        total_amount = float(shipping_cost) + float(tax_amount) - float(discount_amount)
        
        for item_data in items_data:
            item_id = item_data.get('item_id')
            quantity = int(item_data.get('quantity', 1))
            unit_price = float(item_data.get('unit_price', 0))
            
            # Get inventory item
            try:
                inventory_item = InventoryItem.objects.get(id=item_id)
            except InventoryItem.DoesNotExist:
                # Delete the purchase order if item not found
                po.delete()
                return Response({
                    'error': _('Item not found: ') + str(item_id)
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate total price
            total_price = quantity * unit_price
            total_amount += total_price
            
            # Create purchase order item
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                item=inventory_item,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            )
        
        # Update total amount
        po.total_amount = total_amount
        po.save()
        
        return Response({
            'id': po.id,
            'order_number': po.order_number,
            'supplier': {
                'id': po.supplier.id,
                'name': po.supplier.name
            },
            'status': po.status,
            'total_amount': str(po.total_amount),
            'created_at': po.created_at
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def update_purchase_order_status(request, po_id):
    """Update the status of a purchase order"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Get data from request
    new_status = request.data.get('status')
    notes = request.data.get('notes', '')
    
    # Validate status
    valid_statuses = ['draft', 'ordered', 'partial', 'received', 'cancelled']
    if new_status not in valid_statuses:
        return Response({
            'error': _('Invalid status')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if status transition is valid
    if po.status == 'cancelled' and new_status != 'cancelled':
        return Response({
            'error': _('Cannot change status of a cancelled purchase order')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if po.status == 'received' and new_status not in ['received', 'cancelled']:
        return Response({
            'error': _('Cannot change status of a fully received purchase order')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update status
    old_status = po.status
    po.status = new_status
    
    # Add notes if provided
    if notes:
        po.notes = (po.notes + '\n' if po.notes else '') + f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Status changed from {old_status} to {new_status}: {notes}"
    
    # If status is received, update delivery date
    if new_status == 'received' and not po.delivery_date:
        po.delivery_date = timezone.now().date()
    
    # Save changes
    po.save()
    
    return Response({
        'id': po.id,
        'order_number': po.order_number,
        'status': po.status,
        'updated_at': po.updated_at
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffOrReadOnly])
def receive_purchase_order_items(request, po_id):
    """Receive items for a purchase order"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    # Check if purchase order can be received
    if po.status in ['draft', 'cancelled']:
        return Response({
            'error': _('Cannot receive items for a draft or cancelled purchase order')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get data from request
    items_data = request.data.get('items', [])
    notes = request.data.get('notes', '')
    
    if not items_data:
        return Response({
            'error': _('At least one item must be specified')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Process received items
    try:
        all_received = True
        received_items = []
        
        for item_data in items_data:
            po_item_id = item_data.get('po_item_id')
            received_quantity = int(item_data.get('received_quantity', 0))
            
            # Get purchase order item
            try:
                po_item = PurchaseOrderItem.objects.get(id=po_item_id, purchase_order=po)
            except PurchaseOrderItem.DoesNotExist:
                return Response({
                    'error': _('Purchase order item not found: ') + str(po_item_id)
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate received quantity
            remaining_quantity = po_item.quantity - po_item.received_quantity
            if received_quantity <= 0 or received_quantity > remaining_quantity:
                return Response({
                    'error': _('Invalid received quantity for item: ') + po_item.item.name
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update received quantity
            po_item.received_quantity += received_quantity
            
            # Check if fully received
            if po_item.received_quantity >= po_item.quantity:
                po_item.is_received = True
            else:
                all_received = False
            
            # Save changes
            po_item.save()
            
            # Update inventory
            inventory_item = po_item.item
            quantity_before = inventory_item.quantity
            inventory_item.quantity += received_quantity
            inventory_item.save()
            
            # Update item status
            inventory_item.update_status()
            
            # Create inventory transaction
            transaction = InventoryTransaction.objects.create(
                item=inventory_item,
                transaction_type='purchase',
                quantity=received_quantity,
                quantity_before=quantity_before,
                quantity_after=inventory_item.quantity,
                performed_by=request.user,
                reference_id=po.id,
                reference_type='PurchaseOrder',
                notes=f"Received from PO #{po.order_number}"
            )
            
            received_items.append({
                'item_name': inventory_item.name,
                'received_quantity': received_quantity,
                'new_stock_level': inventory_item.quantity
            })
        
        # Update purchase order status
        if all_received:
            po.status = 'received'
            po.delivery_date = timezone.now().date()
        else:
            po.status = 'partial'
        
        # Add notes if provided
        if notes:
            po.notes = (po.notes + '\n' if po.notes else '') + f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Items received: {notes}"
        
        # Save changes
        po.save()
        
        return Response({
            'success': _('Items received successfully'),
            'purchase_order': {
                'id': po.id,
                'order_number': po.order_number,
                'status': po.status
            },
            'received_items': received_items
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
