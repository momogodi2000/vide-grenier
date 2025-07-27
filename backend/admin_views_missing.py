# backend/admin_views_missing.py - MISSING ADMIN VIEWS
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Import models
try:
    from .models import (
        Product, Category, Order, Review, Chat, Message, Notification, 
        Analytics, AdminStock, PickupPoint, ProductImage, Payment, 
        Favorite, SearchHistory, User
    )
    MAIN_MODELS_AVAILABLE = True
except ImportError:
    MAIN_MODELS_AVAILABLE = False

# Import newsletter models
try:
    from .models_newsletter import NewsletterSubscriber, Newsletter
    NEWSLETTER_MODELS_AVAILABLE = True
except ImportError:
    NEWSLETTER_MODELS_AVAILABLE = False

def is_admin(user):
    return user.is_authenticated and user.user_type == 'ADMIN'

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)

# ============= REPORTS VIEWS =============
class AdminReportsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/reports/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if MAIN_MODELS_AVAILABLE:
            context['total_users'] = User.objects.count()
            context['total_products'] = Product.objects.count()
            context['total_orders'] = Order.objects.count()
            context['total_revenue'] = Payment.objects.filter(status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
        return context

class ExportReportsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/reports/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= USER MANAGEMENT VIEWS =============
class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'backend/admin/users/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:users')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_object()
        return context

class AdminUserBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/users/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= PRODUCT MANAGEMENT VIEWS =============
class AdminProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    template_name = 'backend/admin/products/create.html'
    fields = ['title', 'description', 'category', 'price', 'condition', 'city', 'is_negotiable']
    success_url = reverse_lazy('admin:products')
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

class AdminProductDetailView(AdminRequiredMixin, DetailView):
    model = Product
    template_name = 'backend/admin/products/detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    template_name = 'backend/admin/products/edit.html'
    fields = ['title', 'description', 'category', 'price', 'condition', 'city', 'is_negotiable']
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:products')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'backend/admin/products/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:products')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminProductBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/products/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminProductApproveView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/products/approve.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['pk'])
        return context

class AdminProductRejectView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/products/reject.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['pk'])
        return context

# ============= ORDER MANAGEMENT VIEWS =============
class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'backend/admin/orders/detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminOrderUpdateView(AdminRequiredMixin, UpdateView):
    model = Order
    template_name = 'backend/admin/orders/edit.html'
    fields = ['status', 'delivery_address', 'notes']
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:orders')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminOrderCancelView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/orders/cancel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = get_object_or_404(Order, pk=self.kwargs['pk'])
        return context

class ExportOrdersView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/orders/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminOrderBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/orders/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= PAYMENT MANAGEMENT VIEWS =============
class AdminPaymentsView(AdminRequiredMixin, ListView):
    model = Payment
    template_name = 'backend/admin/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 25
    
    def get_queryset(self):
        return Payment.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PaymentDetailView(AdminRequiredMixin, DetailView):
    model = Payment
    template_name = 'backend/admin/payments/detail.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminPaymentRefundView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/payments/refund.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment'] = get_object_or_404(Payment, pk=self.kwargs['pk'])
        return context

class ExportPaymentsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/payments/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminPaymentBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/payments/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= STOCK MANAGEMENT VIEWS =============
class StockAddView(AdminRequiredMixin, CreateView):
    model = AdminStock
    template_name = 'backend/admin/stock/add.html'
    fields = ['product', 'quantity', 'location', 'notes']
    success_url = reverse_lazy('admin:stock')
    
    def form_valid(self, form):
        form.instance.added_by = self.request.user
        return super().form_valid(form)

class StockListView(AdminRequiredMixin, ListView):
    model = AdminStock
    template_name = 'backend/admin/stock/list.html'
    context_object_name = 'stock_items'
    paginate_by = 25
    
    def get_queryset(self):
        return AdminStock.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminStockEditView(AdminRequiredMixin, UpdateView):
    model = AdminStock
    template_name = 'backend/admin/stock/edit.html'
    fields = ['product', 'quantity', 'location', 'notes']
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:stock')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminStockDeleteView(AdminRequiredMixin, DeleteView):
    model = AdminStock
    template_name = 'backend/admin/stock/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:stock')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminStockImportView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/stock/import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminStockExportView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/stock/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminStockMovementsView(AdminRequiredMixin, ListView):
    model = AdminStock
    template_name = 'backend/admin/stock/movements.html'
    context_object_name = 'movements'
    paginate_by = 25
    
    def get_queryset(self):
        return AdminStock.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= PROMOTION MANAGEMENT VIEWS =============
class PromotionsView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/promotions/list.html'
    context_object_name = 'promotions'
    paginate_by = 20
    
    def get_queryset(self):
        # Return empty list since we don't have Promotion model yet
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PromotionCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/promotions/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PromotionEditView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/promotions/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PromotionDeleteView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/promotions/delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PromotionActivateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/promotions/activate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PromotionDeactivateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/promotions/deactivate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= NEWSLETTER MANAGEMENT VIEWS =============
class NewsletterView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/newsletter/list.html'
    context_object_name = 'newsletters'
    paginate_by = 20
    
    def get_queryset(self):
        if NEWSLETTER_MODELS_AVAILABLE:
            return Newsletter.objects.all().order_by('-created_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/newsletter/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterListView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/newsletter/list.html'
    context_object_name = 'newsletters'
    paginate_by = 20
    
    def get_queryset(self):
        if NEWSLETTER_MODELS_AVAILABLE:
            return Newsletter.objects.all().order_by('-created_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterSentView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/newsletter/sent.html'
    context_object_name = 'newsletters'
    paginate_by = 20
    
    def get_queryset(self):
        if NEWSLETTER_MODELS_AVAILABLE:
            return Newsletter.objects.filter(sent=True).order_by('-sent_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterEditView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/newsletter/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterDeleteView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/newsletter/delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterSendView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/newsletter/send.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NewsletterSubscribersView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/newsletter/subscribers.html'
    context_object_name = 'subscribers'
    paginate_by = 50
    
    def get_queryset(self):
        if NEWSLETTER_MODELS_AVAILABLE:
            return NewsletterSubscriber.objects.all().order_by('-subscribed_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= NOTIFICATION MANAGEMENT VIEWS =============
class AdminNotificationsView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 25
    
    def get_queryset(self):
        return Notification.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/notifications/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationListView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 25
    
    def get_queryset(self):
        return Notification.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationEditView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/notifications/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationDeleteView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/notifications/delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationSendView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/notifications/send.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationBulkSendView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/notifications/bulk_send.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= LOYALTY PROGRAM VIEWS =============
class LoyaltyView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/loyalty/list.html'
    context_object_name = 'loyalty_programs'
    paginate_by = 20
    
    def get_queryset(self):
        # Return empty list since we don't have LoyaltyProgram model yet
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/loyalty/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyEditView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/loyalty/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyListView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/loyalty/list.html'
    context_object_name = 'loyalty_programs'
    paginate_by = 20
    
    def get_queryset(self):
        # Return empty list since we don't have LoyaltyProgram model yet
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyDeleteView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/loyalty/delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyPointsView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/loyalty/points.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def get_queryset(self):
        return User.objects.filter(loyalty_points__gt=0).order_by('-loyalty_points')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LoyaltyRewardsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/loyalty/rewards.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= CHAT & COMMUNICATION VIEWS =============
class AdminChatsView(AdminRequiredMixin, ListView):
    model = Chat
    template_name = 'backend/admin/chats/list.html'
    context_object_name = 'chats'
    paginate_by = 25
    
    def get_queryset(self):
        return Chat.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminChatDetailView(AdminRequiredMixin, DetailView):
    model = Chat
    template_name = 'backend/admin/chats/detail.html'
    context_object_name = 'chat'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminChatReplyView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/chats/reply.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chat'] = get_object_or_404(Chat, pk=self.kwargs['pk'])
        return context

class AdminChatBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/chats/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= SYSTEM SETTINGS VIEWS =============
class SystemSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/system.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class BackupView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/backup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LogsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class SecuritySettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/security.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class EmailSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/email.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PaymentSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/payment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class NotificationSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/settings/notification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= PROFILE MANAGEMENT VIEWS =============
class AdminProfileView(AdminRequiredMixin, DetailView):
    model = User
    template_name = 'backend/admin/profile/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminProfileEditView(AdminRequiredMixin, UpdateView):
    model = User
    template_name = 'backend/admin/profile/edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'city']
    success_url = reverse_lazy('admin:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminChangePasswordView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/profile/change_password.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= COMMISSION MANAGEMENT VIEWS =============
class CommissionManagementView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/commissions/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CalculateCommissionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/commissions/calculate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CommissionPayoutView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/commissions/payout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CommissionHistoryView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/commissions/history.html'
    context_object_name = 'commissions'
    paginate_by = 25
    
    def get_queryset(self):
        # Return empty list since we don't have Commission model yet
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= WITHDRAWAL MANAGEMENT VIEWS =============
class WithdrawalManagementView(AdminRequiredMixin, ListView):
    template_name = 'backend/admin/withdrawals/list.html'
    context_object_name = 'withdrawals'
    paginate_by = 25
    
    def get_queryset(self):
        # Return empty list since we don't have Withdrawal model yet
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ApproveWithdrawalView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/withdrawals/approve.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class RejectWithdrawalView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/withdrawals/reject.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class WithdrawalDetailView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/withdrawals/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class WithdrawalBulkActionsView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/withdrawals/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= CATEGORY MANAGEMENT VIEWS =============
class AdminCategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'backend/admin/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 25
    
    def get_queryset(self):
        return Category.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminCategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    template_name = 'backend/admin/categories/create.html'
    fields = ['name', 'description', 'icon', 'is_active']
    success_url = reverse_lazy('admin:categories')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminCategoryEditView(AdminRequiredMixin, UpdateView):
    model = Category
    template_name = 'backend/admin/categories/edit.html'
    fields = ['name', 'description', 'icon', 'is_active']
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:categories')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminCategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'backend/admin/categories/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:categories')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= PICKUP POINT MANAGEMENT VIEWS =============
class AdminPickupPointListView(AdminRequiredMixin, ListView):
    model = PickupPoint
    template_name = 'backend/admin/pickup_points/list.html'
    context_object_name = 'pickup_points'
    paginate_by = 25
    
    def get_queryset(self):
        return PickupPoint.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminPickupPointCreateView(AdminRequiredMixin, CreateView):
    model = PickupPoint
    template_name = 'backend/admin/pickup_points/create.html'
    fields = ['name', 'address', 'city', 'phone', 'email', 'is_active']
    success_url = reverse_lazy('admin:pickup_points')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminPickupPointEditView(AdminRequiredMixin, UpdateView):
    model = PickupPoint
    template_name = 'backend/admin/pickup_points/edit.html'
    fields = ['name', 'address', 'city', 'phone', 'email', 'is_active']
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:pickup_points')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminPickupPointDeleteView(AdminRequiredMixin, DeleteView):
    model = PickupPoint
    template_name = 'backend/admin/pickup_points/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:pickup_points')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= REVIEW MANAGEMENT VIEWS =============
class AdminReviewListView(AdminRequiredMixin, ListView):
    model = Review
    template_name = 'backend/admin/reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 25
    
    def get_queryset(self):
        return Review.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminReviewDetailView(AdminRequiredMixin, DetailView):
    model = Review
    template_name = 'backend/admin/reviews/detail.html'
    context_object_name = 'review'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class AdminReviewApproveView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/reviews/approve.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review'] = get_object_or_404(Review, pk=self.kwargs['pk'])
        return context

class AdminReviewRejectView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/reviews/reject.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review'] = get_object_or_404(Review, pk=self.kwargs['pk'])
        return context

class AdminReviewDeleteView(AdminRequiredMixin, DeleteView):
    model = Review
    template_name = 'backend/admin/reviews/delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('admin:reviews')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= REPORT MANAGEMENT VIEWS =============
class ProductReportsView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'backend/admin/reports/products.html'
    context_object_name = 'products'
    paginate_by = 25
    
    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class UserReportsView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'backend/admin/reports/users.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class OrderReportsView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'backend/admin/reports/orders.html'
    context_object_name = 'orders'
    paginate_by = 25
    
    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class FinancialReportsView(AdminRequiredMixin, ListView):
    model = Payment
    template_name = 'backend/admin/reports/financial.html'
    context_object_name = 'payments'
    paginate_by = 25
    
    def get_queryset(self):
        return Payment.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= API ENDPOINTS =============
class DashboardStatsAPIView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/api/dashboard_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class UserStatsAPIView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/api/user_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class OrderStatsAPIView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/api/order_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class RevenueStatsAPIView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/api/revenue_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= UTILITY PAGES =============
class MaintenanceModeView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class EnableMaintenanceView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/enable_maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class DisableMaintenanceView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/disable_maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ClearCacheView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/clear_cache.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class DatabaseBackupView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/database_backup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class DatabaseRestoreView(AdminRequiredMixin, TemplateView):
    template_name = 'backend/admin/utility/database_restore.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context 