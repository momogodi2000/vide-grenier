# backend/adapters.py - CUSTOM ALLAUTH ADAPTERS FOR USER TYPE REDIRECTS
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for handling user type redirects"""
    
    def get_login_redirect_url(self, request):
        """Redirect users to their appropriate dashboard based on user type"""
        try:
            user = request.user
            
            # For now, redirect to main dashboard redirector
            # This will handle the user type-specific redirects
            return reverse('backend:dashboard')
            
            # Original logic (commented out for testing)
            # if user.user_type == 'CLIENT':
            #     return reverse('client:dashboard')
            # elif user.user_type == 'STAFF':
            #     return reverse('staff:dashboard')
            # elif user.user_type == 'ADMIN':
            #     return reverse('admin:dashboard')
            # else:
            #     return reverse('backend:dashboard')
        except Exception as e:
            # If URL resolution fails, fallback to main dashboard
            print(f"URL resolution error in CustomAccountAdapter: {e}")
            return reverse('backend:dashboard')

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for handling user type redirects"""
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect after connecting social account"""
        return self.get_login_redirect_url(request)
    
    def get_login_redirect_url(self, request):
        """Redirect users to their appropriate dashboard based on user type"""
        try:
            user = request.user
            
            # For now, redirect to main dashboard redirector
            # This will handle the user type-specific redirects
            return reverse('backend:dashboard')
            
            # Original logic (commented out for testing)
            # if user.user_type == 'CLIENT':
            #     return reverse('client:dashboard')
            # elif user.user_type == 'STAFF':
            #     return reverse('staff:dashboard')
            # elif user.user_type == 'ADMIN':
            #     return reverse('admin:dashboard')
            # else:
            #     return reverse('backend:dashboard')
        except Exception as e:
            # If URL resolution fails, fallback to main dashboard
            print(f"URL resolution error in CustomSocialAccountAdapter: {e}")
            return reverse('backend:dashboard') 