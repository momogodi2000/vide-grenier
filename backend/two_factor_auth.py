"""
Two-Factor Authentication System for Vidé-Grenier Kamer
Supports email and SMS verification methods
"""

import random
import string
import hashlib
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
import logging
import os

from .smart_notifications import sms_service, email_service

logger = logging.getLogger(__name__)
User = get_user_model()

class TwoFactorAuth:
    """Two-Factor Authentication system"""
    
    def __init__(self):
        self.enabled = os.environ.get('TWO_FACTOR_AUTH_ENABLED', 'False').lower() == 'true'
        self.methods = os.environ.get('TWO_FACTOR_METHODS', 'email,sms').split(',')
        self.required_for_staff = os.environ.get('TWO_FACTOR_REQUIRED_FOR_STAFF', 'False').lower() == 'true'
        self.required_for_admin = os.environ.get('TWO_FACTOR_REQUIRED_FOR_ADMIN', 'False').lower() == 'true'
        
        # Code settings
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.lockout_duration_minutes = 15
    
    def is_required_for_user(self, user):
        """Check if 2FA is required for a specific user"""
        if not self.enabled:
            return False
        
        if self.required_for_admin and user.user_type == 'ADMIN':
            return True
        
        if self.required_for_staff and user.user_type == 'STAFF':
            return True
        
        # Check if user has enabled 2FA
        return hasattr(user, 'two_factor_enabled') and user.two_factor_enabled
    
    def generate_code(self, length=None):
        """Generate a random numeric code"""
        if length is None:
            length = self.code_length
        
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_code(self, user, method=None):
        """Send verification code via specified method"""
        if not method:
            # Determine best method based on user data
            if 'sms' in self.methods and user.phone and user.phone_verified:
                method = 'sms'
            elif 'email' in self.methods and user.email:
                method = 'email'
            else:
                return {'success': False, 'error': 'No suitable verification method available'}
        
        # Generate code
        code = self.generate_code()
        
        # Store code in cache with expiry
        cache_key = f'2fa_code_{user.id}_{method}'
        cache.set(cache_key, {
            'code': code,
            'attempts': 0,
            'created_at': timezone.now().isoformat()
        }, self.code_expiry_minutes * 60)
        
        # Send code via selected method
        if method == 'sms':
            return self._send_sms_code(user, code)
        elif method == 'email':
            return self._send_email_code(user, code)
        else:
            return {'success': False, 'error': f'Unsupported method: {method}'}
    
    def _send_sms_code(self, user, code):
        """Send verification code via SMS"""
        try:
            message = f"Votre code de vérification VGK: {code}. Valide pendant {self.code_expiry_minutes} minutes."
            
            result = sms_service.send_sms(user.phone, message)
            
            if result.get('success'):
                logger.info(f"2FA SMS code sent to {user.phone}")
                return {
                    'success': True,
                    'method': 'sms',
                    'message': f'Code envoyé par SMS au {user.phone}'
                }
            else:
                logger.error(f"Failed to send 2FA SMS to {user.phone}: {result.get('error')}")
                return {
                    'success': False,
                    'error': f'Erreur envoi SMS: {result.get("error")}'
                }
                
        except Exception as e:
            logger.error(f"Error sending 2FA SMS to {user.phone}: {str(e)}")
            return {
                'success': False,
                'error': f'Erreur technique: {str(e)}'
            }
    
    def _send_email_code(self, user, code):
        """Send verification code via email"""
        try:
            subject = "Code de vérification VGK"
            message = f"""
            Bonjour {user.get_full_name() or user.email},
            
            Votre code de vérification VGK est: {code}
            
            Ce code est valide pendant {self.code_expiry_minutes} minutes.
            
            Si vous n'avez pas demandé ce code, ignorez cet email.
            
            Cordialement,
            L'équipe Vidé-Grenier Kamer
            """
            
            result = email_service.send_email(user.email, subject, message)
            
            if result.get('success'):
                logger.info(f"2FA email code sent to {user.email}")
                return {
                    'success': True,
                    'method': 'email',
                    'message': f'Code envoyé par email à {user.email}'
                }
            else:
                logger.error(f"Failed to send 2FA email to {user.email}: {result.get('error')}")
                return {
                    'success': False,
                    'error': f'Erreur envoi email: {result.get("error")}'
                }
                
        except Exception as e:
            logger.error(f"Error sending 2FA email to {user.email}: {str(e)}")
            return {
                'success': False,
                'error': f'Erreur technique: {str(e)}'
            }
    
    def verify_code(self, user, code, method=None):
        """Verify the provided code"""
        if not method:
            # Try both methods
            for m in ['sms', 'email']:
                if self._verify_code_for_method(user, code, m):
                    return {'success': True, 'method': m}
            return {'success': False, 'error': 'Code invalide'}
        
        return self._verify_code_for_method(user, code, method)
    
    def _verify_code_for_method(self, user, code, method):
        """Verify code for a specific method"""
        cache_key = f'2fa_code_{user.id}_{method}'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return {'success': False, 'error': 'Code expiré ou inexistant'}
        
        # Check if user is locked out
        if cached_data.get('attempts', 0) >= self.max_attempts:
            return {'success': False, 'error': 'Trop de tentatives. Réessayez plus tard.'}
        
        # Increment attempts
        cached_data['attempts'] += 1
        cache.set(cache_key, cached_data, self.code_expiry_minutes * 60)
        
        # Check if code matches
        if cached_data['code'] == code:
            # Success - clear the code
            cache.delete(cache_key)
            
            # Log successful verification
            logger.info(f"2FA verification successful for user {user.id} via {method}")
            
            return {'success': True, 'method': method}
        else:
            # Check if max attempts reached
            if cached_data['attempts'] >= self.max_attempts:
                # Lock out user
                lockout_key = f'2fa_lockout_{user.id}'
                cache.set(lockout_key, True, self.lockout_duration_minutes * 60)
                logger.warning(f"2FA lockout for user {user.id} after {self.max_attempts} failed attempts")
                return {'success': False, 'error': 'Trop de tentatives. Compte temporairement bloqué.'}
            
            return {'success': False, 'error': 'Code incorrect'}
    
    def is_user_locked_out(self, user):
        """Check if user is currently locked out"""
        lockout_key = f'2fa_lockout_{user.id}'
        return cache.get(lockout_key, False)
    
    def get_remaining_attempts(self, user, method):
        """Get remaining attempts for a user"""
        cache_key = f'2fa_code_{user.id}_{method}'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return self.max_attempts
        
        return max(0, self.max_attempts - cached_data.get('attempts', 0))
    
    def resend_code(self, user, method=None):
        """Resend verification code"""
        # Check if user is locked out
        if self.is_user_locked_out(user):
            return {'success': False, 'error': 'Compte temporairement bloqué. Réessayez plus tard.'}
        
        # Clear any existing codes
        for m in ['sms', 'email']:
            cache.delete(f'2fa_code_{user.id}_{m}')
        
        # Send new code
        return self.send_verification_code(user, method)
    
    def disable_2fa(self, user):
        """Disable 2FA for a user"""
        try:
            # Clear any existing codes
            for m in ['sms', 'email']:
                cache.delete(f'2fa_code_{user.id}_{m}')
            
            # Clear lockout
            cache.delete(f'2fa_lockout_{user.id}')
            
            # Update user model if it has 2FA fields
            if hasattr(user, 'two_factor_enabled'):
                user.two_factor_enabled = False
                user.save()
            
            logger.info(f"2FA disabled for user {user.id}")
            return {'success': True, 'message': '2FA désactivé avec succès'}
            
        except Exception as e:
            logger.error(f"Error disabling 2FA for user {user.id}: {str(e)}")
            return {'success': False, 'error': f'Erreur lors de la désactivation: {str(e)}'}
    
    def enable_2fa(self, user, method='email'):
        """Enable 2FA for a user"""
        try:
            # Verify user has required contact info
            if method == 'sms' and not (user.phone and user.phone_verified):
                return {'success': False, 'error': 'Numéro de téléphone vérifié requis pour 2FA SMS'}
            
            if method == 'email' and not user.email:
                return {'success': False, 'error': 'Email requis pour 2FA email'}
            
            # Send initial verification code
            result = self.send_verification_code(user, method)
            
            if result.get('success'):
                # Update user model if it has 2FA fields
                if hasattr(user, 'two_factor_enabled'):
                    user.two_factor_enabled = True
                    user.two_factor_method = method
                    user.save()
                
                logger.info(f"2FA enabled for user {user.id} with method {method}")
                return {
                    'success': True,
                    'message': f'2FA activé avec succès. Code envoyé par {method}.',
                    'method': method
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error enabling 2FA for user {user.id}: {str(e)}")
            return {'success': False, 'error': f'Erreur lors de l\'activation: {str(e)}'}

# Global instance
two_factor_auth = TwoFactorAuth()

# Utility functions
def require_2fa(user):
    """Check if 2FA is required for user"""
    return two_factor_auth.is_required_for_user(user)

def send_2fa_code(user, method=None):
    """Send 2FA verification code"""
    return two_factor_auth.send_verification_code(user, method)

def verify_2fa_code(user, code, method=None):
    """Verify 2FA code"""
    return two_factor_auth.verify_code(user, code, method)

def is_2fa_locked_out(user):
    """Check if user is locked out from 2FA"""
    return two_factor_auth.is_user_locked_out(user)

def resend_2fa_code(user, method=None):
    """Resend 2FA code"""
    return two_factor_auth.resend_code(user, method)

def enable_2fa_for_user(user, method='email'):
    """Enable 2FA for user"""
    return two_factor_auth.enable_2fa(user, method)

def disable_2fa_for_user(user):
    """Disable 2FA for user"""
    return two_factor_auth.disable_2fa(user) 