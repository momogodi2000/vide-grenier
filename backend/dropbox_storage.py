"""
Dropbox Storage Service for Vidé-Grenier Kamer
Handles heavy file storage when database size threshold is reached
"""

import os
import logging
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
import requests
import json
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class DropboxStorageService:
    """Dropbox storage service for heavy files"""
    
    def __init__(self):
        self.app_key = os.environ.get('DROPBOX_APP_KEY')
        self.app_secret = os.environ.get('DROPBOX_APP_SECRET')
        self.access_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
        self.enabled = os.environ.get('DROPBOX_ENABLED', 'False').lower() == 'true'
        self.db_size_threshold_gb = float(os.environ.get('DROPBOX_DB_SIZE_THRESHOLD', '100'))
        
        # Dropbox API endpoints
        self.api_base_url = 'https://api.dropboxapi.com/2'
        self.content_base_url = 'https://content.dropboxapi.com/2'
        
        # File size thresholds
        self.large_file_threshold_mb = 10  # Files larger than 10MB go to Dropbox
        self.image_compression_threshold_mb = 5  # Images larger than 5MB get compressed
    
    def is_enabled(self):
        """Check if Dropbox storage is enabled and configured"""
        return (self.enabled and 
                self.app_key and 
                self.app_secret and 
                self.access_token)
    
    def get_database_size_gb(self):
        """Get current database size in GB"""
        try:
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                return size_bytes / (1024 ** 3)  # Convert to GB
            return 0
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return 0
    
    def should_use_dropbox(self, file_size_bytes=None):
        """Determine if Dropbox should be used based on database size and file size"""
        if not self.is_enabled():
            return False
        
        # Check database size threshold
        db_size_gb = self.get_database_size_gb()
        if db_size_gb >= self.db_size_threshold_gb:
            return True
        
        # Check file size threshold
        if file_size_bytes:
            file_size_mb = file_size_bytes / (1024 ** 2)
            if file_size_mb >= self.large_file_threshold_mb:
                return True
        
        return False
    
    def upload_file(self, file_path, dropbox_path, file_content=None):
        """Upload file to Dropbox"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': json.dumps({
                    'path': dropbox_path,
                    'mode': 'add',
                    'autorename': True,
                    'mute': False
                })
            }
            
            # Upload file
            if file_content:
                response = requests.post(
                    f'{self.content_base_url}/files/upload',
                    headers=headers,
                    data=file_content
                )
            else:
                with open(file_path, 'rb') as f:
                    response = requests.post(
                        f'{self.content_base_url}/files/upload',
                        headers=headers,
                        data=f
                    )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"File uploaded to Dropbox: {dropbox_path}")
                return {
                    'success': True,
                    'path': result.get('path_display'),
                    'id': result.get('id'),
                    'size': result.get('size')
                }
            else:
                logger.error(f"Dropbox upload failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Upload failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error uploading to Dropbox: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, dropbox_path, local_path=None):
        """Download file from Dropbox"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Dropbox-API-Arg': json.dumps({
                    'path': dropbox_path
                })
            }
            
            response = requests.post(
                f'{self.content_base_url}/files/download',
                headers=headers
            )
            
            if response.status_code == 200:
                if local_path:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"File downloaded from Dropbox: {local_path}")
                    return {
                        'success': True,
                        'local_path': local_path,
                        'size': len(response.content)
                    }
                else:
                    return {
                        'success': True,
                        'content': response.content,
                        'size': len(response.content)
                    }
            else:
                logger.error(f"Dropbox download failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Download failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error downloading from Dropbox: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file(self, dropbox_path):
        """Delete file from Dropbox"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': dropbox_path
            }
            
            response = requests.post(
                f'{self.api_base_url}/files/delete_v2',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"File deleted from Dropbox: {dropbox_path}")
                return {'success': True}
            else:
                logger.error(f"Dropbox delete failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Delete failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error deleting from Dropbox: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, dropbox_path):
        """Get file information from Dropbox"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': dropbox_path
            }
            
            response = requests.post(
                f'{self.api_base_url}/files/get_metadata',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'name': result.get('name'),
                    'path': result.get('path_display'),
                    'size': result.get('size'),
                    'modified': result.get('server_modified'),
                    'type': result.get('.tag')
                }
            else:
                logger.error(f"Dropbox metadata failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Metadata failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error getting Dropbox metadata: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_shared_link(self, dropbox_path, expires_in_days=7):
        """Create a shared link for a Dropbox file"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': dropbox_path,
                'settings': {
                    'requested_visibility': 'public',
                    'audience': 'public',
                    'access': 'viewer'
                }
            }
            
            response = requests.post(
                f'{self.api_base_url}/sharing/create_shared_link_with_settings',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                shared_link = result.get('url')
                
                # Convert to direct download link
                direct_link = shared_link.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
                
                return {
                    'success': True,
                    'shared_link': shared_link,
                    'direct_link': direct_link
                }
            else:
                logger.error(f"Dropbox shared link failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Shared link failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error creating Dropbox shared link: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_storage_usage(self):
        """Get Dropbox storage usage"""
        if not self.is_enabled():
            return {'success': False, 'error': 'Dropbox not enabled'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.api_base_url}/users/get_space_usage',
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                used = result.get('used', 0)
                allocated = result.get('allocation', {}).get('allocated', 0)
                
                return {
                    'success': True,
                    'used_bytes': used,
                    'used_gb': used / (1024 ** 3),
                    'allocated_bytes': allocated,
                    'allocated_gb': allocated / (1024 ** 3),
                    'usage_percentage': (used / allocated * 100) if allocated > 0 else 0
                }
            else:
                logger.error(f"Dropbox usage failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Usage check failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error getting Dropbox usage: {e}")
            return {
                'success': False,
                'error': str(e)
            }

@deconstructible
class DropboxStorage(Storage):
    """Django storage backend for Dropbox"""
    
    def __init__(self, location=None, base_url=None):
        self.dropbox_service = DropboxStorageService()
        self.location = location or 'vgk_files'
        self.base_url = base_url
    
    def _open(self, name, mode='rb'):
        """Open file from Dropbox"""
        if not self.dropbox_service.should_use_dropbox():
            return None
        
        dropbox_path = f'/{self.location}/{name}'
        result = self.dropbox_service.download_file(dropbox_path)
        
        if result.get('success'):
            return ContentFile(result.get('content', b''))
        else:
            raise FileNotFoundError(f"File not found in Dropbox: {name}")
    
    def _save(self, name, content):
        """Save file to Dropbox"""
        if not self.dropbox_service.should_use_dropbox(content.size):
            return name
        
        dropbox_path = f'/{self.location}/{name}'
        result = self.dropbox_service.upload_file(
            file_path=None,
            dropbox_path=dropbox_path,
            file_content=content.read()
        )
        
        if result.get('success'):
            return name
        else:
            raise Exception(f"Failed to upload to Dropbox: {result.get('error')}")
    
    def delete(self, name):
        """Delete file from Dropbox"""
        if not self.dropbox_service.should_use_dropbox():
            return
        
        dropbox_path = f'/{self.location}/{name}'
        self.dropbox_service.delete_file(dropbox_path)
    
    def exists(self, name):
        """Check if file exists in Dropbox"""
        if not self.dropbox_service.should_use_dropbox():
            return False
        
        dropbox_path = f'/{self.location}/{name}'
        result = self.dropbox_service.get_file_info(dropbox_path)
        return result.get('success', False)
    
    def url(self, name):
        """Get URL for file in Dropbox"""
        if not self.dropbox_service.should_use_dropbox():
            return None
        
        dropbox_path = f'/{self.location}/{name}'
        result = self.dropbox_service.create_shared_link(dropbox_path)
        
        if result.get('success'):
            return result.get('direct_link')
        else:
            return None
    
    def size(self, name):
        """Get file size from Dropbox"""
        if not self.dropbox_service.should_use_dropbox():
            return 0
        
        dropbox_path = f'/{self.location}/{name}'
        result = self.dropbox_service.get_file_info(dropbox_path)
        
        if result.get('success'):
            return result.get('size', 0)
        else:
            return 0

# Global instance
dropbox_storage_service = DropboxStorageService()

# Utility functions
def should_use_dropbox_storage(file_size_bytes=None):
    """Check if Dropbox storage should be used"""
    return dropbox_storage_service.should_use_dropbox(file_size_bytes)

def upload_to_dropbox(file_path, dropbox_path, file_content=None):
    """Upload file to Dropbox"""
    return dropbox_storage_service.upload_file(file_path, dropbox_path, file_content)

def download_from_dropbox(dropbox_path, local_path=None):
    """Download file from Dropbox"""
    return dropbox_storage_service.download_file(dropbox_path, local_path)

def delete_from_dropbox(dropbox_path):
    """Delete file from Dropbox"""
    return dropbox_storage_service.delete_file(dropbox_path)

def get_dropbox_file_info(dropbox_path):
    """Get file information from Dropbox"""
    return dropbox_storage_service.get_file_info(dropbox_path)

def create_dropbox_shared_link(dropbox_path, expires_in_days=7):
    """Create shared link for Dropbox file"""
    return dropbox_storage_service.create_shared_link(dropbox_path, expires_in_days)

def get_dropbox_storage_usage():
    """Get Dropbox storage usage"""
    return dropbox_storage_service.get_storage_usage()

def get_database_size_gb():
    """Get current database size in GB"""
    return dropbox_storage_service.get_database_size_gb() 