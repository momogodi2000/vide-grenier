import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# JWT Settings
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)

def generate_jwt_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'user_type': user.user_type,
        'exp': datetime.utcnow() + JWT_ACCESS_TOKEN_LIFETIME,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def generate_refresh_token(user):
    """Generate refresh token for user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh)

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError('Token has expired')
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError('Invalid token')

def get_user_from_token(token):
    """Get user from JWT token"""
    try:
        payload = verify_jwt_token(token)
        user = User.objects.get(id=payload['user_id'])
        return user
    except (jwt.InvalidTokenError, User.DoesNotExist):
        return None

def refresh_jwt_token(refresh_token):
    """Refresh JWT token using refresh token"""
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        return access_token
    except Exception:
        return None

def generate_tokens_for_user(user):
    """Generate both access and refresh tokens for user"""
    access_token = generate_jwt_token(user)
    refresh_token = generate_refresh_token(user)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': int(JWT_ACCESS_TOKEN_LIFETIME.total_seconds())
    }

def validate_token_format(token):
    """Validate token format"""
    if not token or not isinstance(token, str):
        return False
    
    # Check if token has the right format (3 parts separated by dots)
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    return True

def decode_token_payload(token):
    """Decode token payload without verification (for debugging)"""
    try:
        # Decode without verification
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        return None 