from django.urls import path
from . import views

app_name = 'medical_inventory'

urlpatterns = [
    # Category endpoints
    path('categories/', views.get_inventory_categories, name='category-list'),
    path('categories/<int:category_id>/', views.get_category_detail, name='category-detail'),
    path('categories/create/', views.create_category, name='category-create'),
    path('categories/<int:category_id>/update/', views.update_category, name='category-update'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='category-delete'),
    
    # Inventory item endpoints
    path('items/', views.get_inventory_items, name='item-list'),
    path('items/<int:item_id>/', views.get_item_detail, name='item-detail'),
    path('items/create/', views.create_item, name='item-create'),
    path('items/<int:item_id>/update/', views.update_item, name='item-update'),
    path('items/<int:item_id>/adjust/', views.adjust_inventory, name='item-adjust'),
    path('items/<int:item_id>/delete/', views.delete_item, name='item-delete'),
    
    # Supplier endpoints
    path('suppliers/', views.get_suppliers, name='supplier-list'),
    path('suppliers/<int:supplier_id>/', views.get_supplier_detail, name='supplier-detail'),
    path('suppliers/create/', views.create_supplier, name='supplier-create'),
    path('suppliers/<int:supplier_id>/update/', views.update_supplier, name='supplier-update'),
    path('suppliers/<int:supplier_id>/delete/', views.delete_supplier, name='supplier-delete'),
    
    # Purchase order endpoints
    path('purchase-orders/', views.get_purchase_orders, name='purchase-order-list'),
    path('purchase-orders/<int:po_id>/', views.get_purchase_order_detail, name='purchase-order-detail'),
    path('purchase-orders/create/', views.create_purchase_order, name='purchase-order-create'),
    path('purchase-orders/<int:po_id>/update-status/', views.update_purchase_order_status, name='purchase-order-update-status'),
    path('purchase-orders/<int:po_id>/receive-items/', views.receive_purchase_order_items, name='purchase-order-receive-items'),
]
