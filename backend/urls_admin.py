# backend/urls_admin.py - COMPLETE ADMIN-SPECIFIC URLs FOR VGK
from django.urls import path, include
from . import views_admin

app_name = 'admin_panel'

urlpatterns = [
    # ============= DASHBOARD =============
    path('', views_admin.admin_dashboard, name='dashboard'),
    
    # ============= ANALYTICS & REPORTS =============
    path('analytics/', views_admin.AdminAnalyticsView.as_view(), name='analytics'),
    path('analytics/dashboard/', views_admin.AdminAnalyticsView.as_view(), name='analytics_dashboard'),
    path('reports/', views_admin.admin_dashboard, name='reports'),  # Temporary fix
    path('reports/export/', views_admin.ExportReportsView.as_view(), name='export_reports'),
    
    # ============= USER MANAGEMENT =============
    path('users/', views_admin.AdminUserListView.as_view(), name='users'),
    path('users/list/', views_admin.AdminUserListView.as_view(), name='admin_user_list'),
    path('users/create/', views_admin.AdminUserCreateView.as_view(), name='user_create'),
    path('users/<uuid:pk>/', views_admin.AdminUserDetailView.as_view(), name='user_detail'),
    path('users/<uuid:pk>/edit/', views_admin.AdminUserUpdateView.as_view(), name='user_edit'),
    path('users/<uuid:pk>/delete/', views_admin.AdminUserDeleteView.as_view(), name='user_delete'),
    path('users/<uuid:pk>/toggle-status/', views_admin.admin_user_toggle_status, name='user_toggle_status'),
    path('users/bulk-actions/', views_admin.AdminUserBulkActionsView.as_view(), name='user_bulk_actions'),
    path('export/users/', views_admin.admin_export_users, name='export_users'),
    path('ajax/quick-action/', views_admin.admin_quick_action, name='admin_quick_action'),
    
    # ============= PRODUCT MANAGEMENT =============
    path('products/', views_admin.AdminProductListView.as_view(), name='products'),
    path('products/create/', views_admin.AdminProductCreateView.as_view(), name='product_create'),
    path('products/<uuid:pk>/', views_admin.AdminProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:pk>/edit/', views_admin.AdminProductUpdateView.as_view(), name='product_edit'),
    path('products/<uuid:pk>/delete/', views_admin.AdminProductDeleteView.as_view(), name='product_delete'),
    path('products/<uuid:pk>/delete-ajax/', views_admin.admin_product_delete_ajax, name='product_delete_ajax'),
    path('products/<uuid:pk>/approve/', views_admin.ProductApprovalView.as_view(), name='product_approve'),
    path('products/<uuid:pk>/reject/', views_admin.ProductRejectionView.as_view(), name='product_reject'),
    path('products/<uuid:pk>/contact-seller/', views_admin.ProductContactSellerView.as_view(), name='product_contact_seller'),
    
    # ============= PENDING PRODUCTS APPROVAL =============
    path('products/pending/', views_admin.AdminPendingProductsView.as_view(), name='pending_products'),
    path('products/<uuid:pk>/approval/', views_admin.AdminProductApprovalView.as_view(), name='product_approval'),
    path('products/<uuid:pk>/approve-action/', views_admin.admin_product_approve_action, name='product_approve_action'),
    
    # ============= ORDER MANAGEMENT =============
    path('orders/', views_admin.AdminOrderListView.as_view(), name='orders'),
    path('orders/<uuid:pk>/', views_admin.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/process/', views_admin.OrderProcessingView.as_view(), name='order_process'),
    path('orders/<uuid:pk>/update-status/', views_admin.OrderStatusUpdateView.as_view(), name='order_update_status'),
    path('orders/export/', views_admin.ExportOrdersView.as_view(), name='export_orders'),
    path('orders/bulk-actions/', views_admin.AdminOrderBulkActionsView.as_view(), name='order_bulk_actions'),
    
    # ============= PAYMENT MANAGEMENT =============
    path('payments/', views_admin.AdminPaymentsView.as_view(), name='payments'),
    path('payments/<uuid:pk>/', views_admin.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<uuid:pk>/refund/', views_admin.AdminPaymentRefundView.as_view(), name='payment_refund'),
    path('payments/export/', views_admin.ExportPaymentsView.as_view(), name='export_payments'),
    path('payments/bulk-actions/', views_admin.AdminPaymentBulkActionsView.as_view(), name='payment_bulk_actions'),
    
    # ============= STOCK MANAGEMENT =============
    path('stock/', views_admin.AdminStockView.as_view(), name='stock'),
    path('stock/calculate/', views_admin.StockCalculateView.as_view(), name='stock_calculate'),
    path('stock/alerts/', views_admin.StockAlertsView.as_view(), name='stock_alerts'),
    path('stock/add/', views_admin.StockAddView.as_view(), name='stock_add'),
    path('stock/list/', views_admin.StockListView.as_view(), name='stock_list'),
    path('stock/<uuid:pk>/edit/', views_admin.AdminStockEditView.as_view(), name='stock_edit'),
    path('stock/<uuid:pk>/delete/', views_admin.AdminStockDeleteView.as_view(), name='stock_delete'),
    path('stock/import/', views_admin.AdminStockImportView.as_view(), name='stock_import'),
    path('stock/export/', views_admin.AdminStockExportView.as_view(), name='stock_export'),
    path('stock/movements/', views_admin.AdminStockMovementsView.as_view(), name='stock_movements'),
    
    # ============= PROMOTIONS & MARKETING =============
    path('promotions/', views_admin.PromotionsView.as_view(), name='promotions'),
    path('promotions/create/', views_admin.PromotionCreateView.as_view(), name='promotion_create'),
    path('promotions/create/', views_admin.PromotionCreateView.as_view(), name='admin_promotion_create'),
    path('promotions/<uuid:pk>/edit/', views_admin.PromotionEditView.as_view(), name='promotion_edit'),
    path('promotions/<uuid:pk>/delete/', views_admin.PromotionDeleteView.as_view(), name='promotion_delete'),
    path('promotions/<uuid:pk>/activate/', views_admin.PromotionActivateView.as_view(), name='promotion_activate'),
    path('promotions/<uuid:pk>/deactivate/', views_admin.PromotionDeactivateView.as_view(), name='promotion_deactivate'),
    
    # ============= NEWSLETTER MANAGEMENT =============
    path('newsletter/', views_admin.NewsletterView.as_view(), name='newsletter'),
    path('newsletter/create/', views_admin.NewsletterCreateView.as_view(), name='newsletter_create'),
    path('newsletter/list/', views_admin.NewsletterListView.as_view(), name='newsletter_list'),
    path('newsletter/sent/', views_admin.NewsletterSentView.as_view(), name='newsletter_sent'),
    path('newsletter/<uuid:pk>/edit/', views_admin.NewsletterEditView.as_view(), name='newsletter_edit'),
    path('newsletter/<uuid:pk>/delete/', views_admin.NewsletterDeleteView.as_view(), name='newsletter_delete'),
    path('newsletter/<uuid:pk>/send/', views_admin.NewsletterSendView.as_view(), name='newsletter_send'),
    path('newsletter/send/', views_admin.NewsletterSendView.as_view(), name='admin_newsletter_send'),
    path('newsletter/subscribers/', views_admin.NewsletterSubscribersView.as_view(), name='newsletter_subscribers'),
    
    # ============= NOTIFICATION MANAGEMENT =============
    path('notifications/', views_admin.AdminNotificationsView.as_view(), name='notifications'),
    path('notifications/create/', views_admin.NotificationCreateView.as_view(), name='notification_create'),
    path('notifications/create/', views_admin.NotificationCreateView.as_view(), name='admin_notification_create'),
    path('notifications/list/', views_admin.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:pk>/edit/', views_admin.NotificationEditView.as_view(), name='notification_edit'),
    path('notifications/<uuid:pk>/delete/', views_admin.NotificationDeleteView.as_view(), name='notification_delete'),
    path('notifications/<uuid:pk>/send/', views_admin.NotificationSendView.as_view(), name='notification_send'),
    path('notifications/bulk-send/', views_admin.NotificationBulkSendView.as_view(), name='notification_bulk_send'),
    
    # ============= LOYALTY PROGRAM =============
    path('loyalty/', views_admin.LoyaltyView.as_view(), name='loyalty'),
    path('loyalty/create/', views_admin.LoyaltyCreateView.as_view(), name='loyalty_create'),
    path('loyalty/create/', views_admin.LoyaltyCreateView.as_view(), name='admin_loyalty_create'),
    path('loyalty/edit/', views_admin.LoyaltyEditView.as_view(), name='loyalty_edit'),
    path('loyalty/list/', views_admin.LoyaltyListView.as_view(), name='loyalty_list'),
    path('loyalty/<uuid:pk>/edit/', views_admin.LoyaltyEditView.as_view(), name='loyalty_edit'),
    path('loyalty/<uuid:pk>/delete/', views_admin.LoyaltyDeleteView.as_view(), name='loyalty_delete'),
    path('loyalty/points/', views_admin.LoyaltyPointsView.as_view(), name='loyalty_points'),
    path('loyalty/rewards/', views_admin.LoyaltyRewardsView.as_view(), name='loyalty_rewards'),
    
    # ============= CHAT SYSTEM =============
    path('chat/', views_admin.AdminChatListView.as_view(), name='chats'),
    path('chat/<uuid:user_id>/', views_admin.AdminChatDetailView.as_view(), name='chat_detail'),
    path('chat/<uuid:user_id>/messages/', views_admin.AdminChatMessagesView.as_view(), name='chat_messages'),
    path('chat/<uuid:user_id>/send/', views_admin.AdminChatSendView.as_view(), name='chat_send'),
    
    # ============= EMAIL SYSTEM =============
    path('email/send/', views_admin.AdminEmailSendView.as_view(), name='email_send'),
    path('email/templates/', views_admin.AdminEmailTemplatesView.as_view(), name='email_templates'),
    
    # ============= SYSTEM SETTINGS =============
    path('settings/', views_admin.SystemSettingsView.as_view(), name='settings'),
    path('settings/backup/', views_admin.BackupView.as_view(), name='backup'),
    path('settings/logs/', views_admin.LogsView.as_view(), name='logs'),
    path('settings/security/', views_admin.SecuritySettingsView.as_view(), name='security_settings'),
    path('settings/email/', views_admin.EmailSettingsView.as_view(), name='email_settings'),
    path('settings/payment/', views_admin.PaymentSettingsView.as_view(), name='payment_settings'),
    path('settings/notification/', views_admin.NotificationSettingsView.as_view(), name='notification_settings'),
    
    # ============= PROFILE MANAGEMENT =============
    path('profile/', views_admin.AdminProfileView.as_view(), name='profile'),
    path('profile/edit/', views_admin.AdminProfileEditView.as_view(), name='profile_edit'),
    path('profile/change-password/', views_admin.AdminChangePasswordView.as_view(), name='change_password'),
    
    # ============= COMMISSION MANAGEMENT =============
    path('commissions/', views_admin.AdminCommissionView.as_view(), name='commissions'),
    path('commissions/calculate/', views_admin.CommissionCalculateView.as_view(), name='commission_calculate'),
    path('commissions/payout/', views_admin.CommissionPayoutView.as_view(), name='commission_payout'),
    path('commissions/report/', views_admin.CommissionReportView.as_view(), name='commission_report'),
    
    # ============= WITHDRAWAL MANAGEMENT =============
    path('withdrawals/', views_admin.WithdrawalManagementView.as_view(), name='withdrawals'),
    path('withdrawals/<uuid:pk>/approve/', views_admin.ApproveWithdrawalView.as_view(), name='approve_withdrawal'),
    path('withdrawals/<uuid:pk>/reject/', views_admin.RejectWithdrawalView.as_view(), name='reject_withdrawal'),
    path('withdrawals/<uuid:pk>/detail/', views_admin.WithdrawalDetailView.as_view(), name='withdrawal_detail'),
    path('withdrawals/bulk-actions/', views_admin.WithdrawalBulkActionsView.as_view(), name='withdrawal_bulk_actions'),
    
    # ============= CATEGORY MANAGEMENT =============
    path('categories/', views_admin.AdminCategoryListView.as_view(), name='categories'),
    path('categories/create/', views_admin.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<uuid:pk>/edit/', views_admin.CategoryEditView.as_view(), name='category_edit'),
    path('categories/<uuid:pk>/delete/', views_admin.CategoryDeleteView.as_view(), name='category_delete'),
    
    # ============= PICKUP POINT MANAGEMENT =============
    path('pickup-points/', views_admin.AdminPickupPointListView.as_view(), name='pickup_points'),
    path('pickup-points/create/', views_admin.AdminPickupPointCreateView.as_view(), name='pickup_point_create'),
    path('pickup-points/<uuid:pk>/', views_admin.PickupPointDetailView.as_view(), name='pickup_point_detail'),
    path('pickup-points/<uuid:pk>/edit/', views_admin.PickupPointEditView.as_view(), name='pickup_point_edit'),
    path('pickup-points/<uuid:pk>/delete/', views_admin.AdminPickupPointDeleteView.as_view(), name='pickup_point_delete'),
    path('pickup-points/<uuid:pk>/toggle-status/', views_admin.PickupPointToggleStatusView.as_view(), name='pickup_point_toggle_status'),
    
    # ============= REVIEW MANAGEMENT =============
    path('reviews/', views_admin.AdminReviewListView.as_view(), name='reviews'),
    path('reviews/<uuid:pk>/', views_admin.AdminReviewDetailView.as_view(), name='review_detail'),
    path('reviews/<uuid:pk>/approve/', views_admin.AdminReviewApproveView.as_view(), name='review_approve'),
    path('reviews/<uuid:pk>/reject/', views_admin.AdminReviewRejectView.as_view(), name='review_reject'),
    path('reviews/<uuid:pk>/delete/', views_admin.AdminReviewDeleteView.as_view(), name='review_delete'),
    
    # ============= REPORT MANAGEMENT =============
    path('reports/products/', views_admin.ProductReportsView.as_view(), name='product_reports'),
    path('reports/users/', views_admin.UserReportsView.as_view(), name='user_reports'),
    path('reports/orders/', views_admin.OrderReportsView.as_view(), name='order_reports'),
    path('reports/financial/', views_admin.FinancialReportsView.as_view(), name='financial_reports'),
    
    # ============= API ENDPOINTS =============
    path('api/dashboard-stats/', views_admin.DashboardStatsAPIView.as_view(), name='dashboard_stats_api'),
    path('api/user-stats/', views_admin.UserStatsAPIView.as_view(), name='user_stats_api'),
    path('api/order-stats/', views_admin.OrderStatsAPIView.as_view(), name='order_stats_api'),
    path('api/revenue-stats/', views_admin.RevenueStatsAPIView.as_view(), name='revenue_stats_api'),
    
    # ============= UTILITY PAGES =============
    path('maintenance/', views_admin.MaintenanceModeView.as_view(), name='maintenance'),
    path('maintenance/enable/', views_admin.EnableMaintenanceView.as_view(), name='enable_maintenance'),
    path('maintenance/disable/', views_admin.DisableMaintenanceView.as_view(), name='disable_maintenance'),
    path('cache/clear/', views_admin.ClearCacheView.as_view(), name='clear_cache'),
    path('database/backup/', views_admin.DatabaseBackupView.as_view(), name='database_backup'),
    path('database/restore/', views_admin.DatabaseRestoreView.as_view(), name='database_restore'),
    
    # ============= DEBUG URL (temporary) =============
    path('debug/', views_admin.admin_debug_view, name='debug_profile'),
    path('test-profile/', views_admin.admin_test_profile_view, name='test_profile'),
] 