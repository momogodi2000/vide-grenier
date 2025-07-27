# backend/urls_staff.py - STAFF-SPECIFIC URL PATTERNS
from django.urls import path
from . import views_staff

app_name = 'staff'

urlpatterns = [
    # ============= DASHBOARD =============
    path('', views_staff.StaffDashboardView.as_view(), name='dashboard'),
    
    # ============= PROFILE MANAGEMENT =============
    path('profile/', views_staff.StaffProfileView.as_view(), name='profile'),
    path('profile/edit/', views_staff.StaffProfileEditView.as_view(), name='profile_edit'),
    
    # ============= ORDER PROCESSING =============
    path('orders/', views_staff.OrderProcessingView.as_view(), name='order_processing'),
    path('orders/<uuid:pk>/', views_staff.OrderDetailView.as_view(), name='order_detail'),
    path('orders/process/', views_staff.process_pickup, name='process_order'),
    
    # ============= POINT OF SALE =============
    path('pos/', views_staff.POSSystemView.as_view(), name='pos_system'),
    path('pos/process-sale/', views_staff.process_pickup, name='process_sale'),
    
    # ============= INVENTORY MANAGEMENT =============
    path('inventory/', views_staff.InventoryDashboardView.as_view(), name='inventory_dashboard'),
    path('inventory/list/', views_staff.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/receive/', views_staff.StockReceivingView.as_view(), name='stock_receiving'),
    path('inventory/movements/', views_staff.InventoryMovementListView.as_view(), name='inventory_movements'),
    path('inventory/update/', views_staff.update_inventory, name='update_inventory'),
    path('inventory/receive-stock/', views_staff.receive_stock, name='receive_stock'),
    
    # ============= TASK MANAGEMENT =============
    path('tasks/', views_staff.StaffTaskListView.as_view(), name='staff_tasks'),
    path('tasks/update-status/', views_staff.update_task_status, name='update_task_status'),
    
    # ============= QR CODE SYSTEM =============
    path('qr-scanner/', views_staff.QRScannerView.as_view(), name='qr_scanner'),
    path('qr/scan/', views_staff.process_qr_scan, name='process_qr_scan'),
    path('qr/generate/', views_staff.generate_qr_code, name='generate_qr_code'),
    path('qr/scan-process/', views_staff.scan_qr_code, name='scan_qr_code'),
    
    # ============= CUSTOMER SERVICE =============
    path('customer-service/', views_staff.CustomerServiceView.as_view(), name='customer_service'),
    path('customer-service/contact/', views_staff.contact_customer, name='contact_customer'),
    path('customer-service/assistance/', views_staff.customer_assistance, name='customer_assistance'),
    
    # ============= PERFORMANCE & ANALYTICS =============
    path('performance/', views_staff.StaffPerformanceView.as_view(), name='staff_performance'),
    path('analytics/', views_staff.PerformanceAnalyticsView.as_view(), name='performance_analytics'),
    path('reports/generate/', views_staff.generate_report, name='generate_report'),
    
    # ============= PICKUP MANAGEMENT =============
    path('pickups/', views_staff.PickupManagementView.as_view(), name='pickup_management'),
    path('pickups/process/', views_staff.process_pickup, name='process_pickup'),
] 