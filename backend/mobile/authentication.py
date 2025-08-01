from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .jwt_utils import get_user_from_token

User = get_user_model()

class MobileJWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT authentication for mobile API"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            user = get_user_from_token(token)
            if user and user.is_active:
                return (user, token)
            else:
                raise AuthenticationFailed('Invalid token')
        except Exception:
            raise AuthenticationFailed('Invalid token')
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"'

class MobileOptionalJWTAuthentication(authentication.BaseAuthentication):
    """Optional JWT authentication for mobile API"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            user = get_user_from_token(token)
            if user and user.is_active:
                return (user, token)
            else:
                return None
        except Exception:
            return None
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"' 