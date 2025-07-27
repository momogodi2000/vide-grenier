# backend/views_enhanced.py - ENHANCED VIEWS FOR USER-TYPE SEPARATION
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.contrib import messages
from django.urls import reverse

class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirect users to their appropriate dashboard based on user type"""
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            if user.user_type == 'CLIENT':
                return redirect('/client/')
            elif user.user_type == 'STAFF':
                return redirect('/staff/') 
            elif user.user_type == 'ADMIN':
                return redirect('/admin-panel/')
            else:
                messages.error(request, 'Type d\'utilisateur non reconnu.')
                return redirect('backend:home')
        except Exception as e:
            # Fallback in case of any URL resolution issues
            messages.error(request, f'Erreur de redirection: {str(e)}')
            return redirect('backend:home')

class UserTypeRequiredMixin:
    """Mixin to ensure user has correct user_type for accessing view"""
    required_user_type = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('backend:login')
            
        if self.required_user_type and request.user.user_type != self.required_user_type:
            messages.error(request, 'Vous n\'avez pas l\'autorisation d\'accéder à cette page.')
            # Redirect to their appropriate dashboard
            if request.user.user_type == 'CLIENT':
                return redirect('/client/')
            elif request.user.user_type == 'STAFF':
                return redirect('/staff/')
            elif request.user.user_type == 'ADMIN':
                return redirect('/admin-panel/')
            else:
                return redirect('backend:home')
                
        return super().dispatch(request, *args, **kwargs)

class ClientRequiredMixin(UserTypeRequiredMixin):
    """Mixin for views that require CLIENT user type"""
    required_user_type = 'CLIENT'

class StaffRequiredMixin(UserTypeRequiredMixin):
    """Mixin for views that require STAFF user type"""
    required_user_type = 'STAFF'

class AdminRequiredMixin(UserTypeRequiredMixin):
    """Mixin for views that require ADMIN user type"""
    required_user_type = 'ADMIN' 