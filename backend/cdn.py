# backend/cdn.py
"""
CDN Configuration and Management for VGK
Handles static file optimization and CDN integration
"""

import os
import hashlib
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class CDNManager:
    """Manages CDN operations and static file optimization"""
    
    def __init__(self):
        self.cdn_url = settings.VGK_SETTINGS.get('CDN_URL', '')
        self.enabled = bool(self.cdn_url)
    
    def get_cdn_url(self, path):
        """Get full CDN URL for a file path"""
        if not self.enabled:
            return path
        
        # Remove leading slash if present
        if path.startswith('/'):
            path = path[1:]
        
        return f"{self.cdn_url.rstrip('/')}/{path}"
    
    def optimize_image(self, image_path, quality=85, max_size=(1200, 1200)):
        """Optimize image for web delivery"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(image_path, 'JPEG', quality=quality, optimize=True)
                
                logger.info(f"Optimized image: {image_path}")
                return True
        except Exception as e:
            logger.error(f"Error optimizing image {image_path}: {e}")
            return False
    
    def generate_webp_version(self, image_path):
        """Generate WebP version of image for better compression"""
        try:
            webp_path = image_path.rsplit('.', 1)[0] + '.webp'
            
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.save(webp_path, 'WEBP', quality=85, optimize=True)
                
                logger.info(f"Generated WebP version: {webp_path}")
                return webp_path
        except Exception as e:
            logger.error(f"Error generating WebP for {image_path}: {e}")
            return None
    
    def optimize_product_images(self, product):
        """Optimize all images for a product"""
        try:
            for image in product.images.all():
                if image.image:
                    # Optimize original image
                    self.optimize_image(image.image.path)
                    
                    # Generate WebP version
                    webp_path = self.generate_webp_version(image.image.path)
                    
                    # Update image record with WebP path
                    if webp_path:
                        image.webp_path = webp_path
                        image.save(update_fields=['webp_path'])
            
            logger.info(f"Optimized images for product: {product.title}")
            return True
        except Exception as e:
            logger.error(f"Error optimizing images for product {product.id}: {e}")
            return False
    
    def get_optimized_image_url(self, image_path, format='auto'):
        """Get optimized image URL with format detection"""
        if not self.enabled:
            return image_path
        
        # Check if WebP is supported
        if format == 'auto':
            # In a real implementation, you'd check browser support
            # For now, we'll use WebP for better compression
            format = 'webp'
        
        if format == 'webp':
            webp_path = image_path.rsplit('.', 1)[0] + '.webp'
            if os.path.exists(webp_path):
                return self.get_cdn_url(webp_path)
        
        return self.get_cdn_url(image_path)
    
    def cache_bust_url(self, url):
        """Add cache busting parameter to URL"""
        if not self.enabled:
            return url
        
        # Add timestamp for cache busting
        timestamp = int(timezone.now().timestamp())
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}v={timestamp}"
    
    def get_static_url(self, path):
        """Get CDN URL for static files"""
        return self.get_cdn_url(f"static/{path}")
    
    def get_media_url(self, path):
        """Get CDN URL for media files"""
        return self.get_cdn_url(f"media/{path}")


class ImageOptimizer:
    """Handles image optimization and processing"""
    
    def __init__(self):
        self.supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_image(self, image_file):
        """Validate uploaded image"""
        try:
            # Check file size
            if image_file.size > self.max_file_size:
                return False, "File size too large (max 10MB)"
            
            # Check file format
            file_extension = image_file.name.split('.')[-1].lower()
            if file_extension not in self.supported_formats:
                return False, f"Unsupported format. Supported: {', '.join(self.supported_formats)}"
            
            # Validate image content
            with Image.open(image_file) as img:
                img.verify()
            
            return True, "Valid image"
        except Exception as e:
            return False, f"Invalid image: {str(e)}"
    
    def process_uploaded_image(self, image_file, target_path):
        """Process and optimize uploaded image"""
        try:
            with Image.open(image_file) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (1200, 1200)
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(target_path, 'JPEG', quality=85, optimize=True)
                
                return True, "Image processed successfully"
        except Exception as e:
            return False, f"Error processing image: {str(e)}"
    
    def create_thumbnails(self, image_path, sizes=None):
        """Create thumbnails for different sizes"""
        if sizes is None:
            sizes = {
                'small': (150, 150),
                'medium': (300, 300),
                'large': (600, 600)
            }
        
        thumbnails = {}
        
        try:
            with Image.open(image_path) as img:
                for size_name, dimensions in sizes.items():
                    thumbnail = img.copy()
                    thumbnail.thumbnail(dimensions, Image.Resampling.LANCZOS)
                    
                    # Generate thumbnail path
                    base_path = image_path.rsplit('.', 1)[0]
                    extension = image_path.rsplit('.', 1)[1]
                    thumbnail_path = f"{base_path}_{size_name}.{extension}"
                    
                    # Save thumbnail
                    thumbnail.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
                    thumbnails[size_name] = thumbnail_path
            
            return thumbnails
        except Exception as e:
            logger.error(f"Error creating thumbnails for {image_path}: {e}")
            return {}


class StaticFileOptimizer:
    """Handles static file optimization"""
    
    def __init__(self):
        self.cdn_manager = CDNManager()
    
    def optimize_css(self, css_content):
        """Minify CSS content"""
        # Simple CSS minification (in production, use a proper CSS minifier)
        import re
        
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s*', '{', css_content)
        css_content = re.sub(r'}\s*', '}', css_content)
        
        return css_content.strip()
    
    def optimize_js(self, js_content):
        """Minify JavaScript content"""
        # Simple JS minification (in production, use a proper JS minifier)
        import re
        
        # Remove comments
        js_content = re.sub(r'//.*?\n', '\n', js_content)
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace
        js_content = re.sub(r'\s+', ' ', js_content)
        
        return js_content.strip()
    
    def generate_file_hash(self, file_path):
        """Generate hash for file for cache busting"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            return file_hash
        except Exception as e:
            logger.error(f"Error generating hash for {file_path}: {e}")
            return None
    
    def get_optimized_static_url(self, static_path):
        """Get optimized static file URL with cache busting"""
        if not self.cdn_manager.enabled:
            return static_path
        
        # Generate hash for cache busting
        file_path = os.path.join(settings.STATIC_ROOT, static_path)
        if os.path.exists(file_path):
            file_hash = self.generate_file_hash(file_path)
            if file_hash:
                base_path = static_path.rsplit('.', 1)[0]
                extension = static_path.rsplit('.', 1)[1]
                return self.cdn_manager.get_static_url(f"{base_path}.{file_hash}.{extension}")
        
        return self.cdn_manager.get_static_url(static_path)


# Global instances
cdn_manager = CDNManager()
image_optimizer = ImageOptimizer()
static_optimizer = StaticFileOptimizer()


def get_cdn_url(path):
    """Convenience function to get CDN URL"""
    return cdn_manager.get_cdn_url(path)


def optimize_product_image(product_image):
    """Convenience function to optimize product image"""
    return cdn_manager.optimize_product_images(product_image.product)


def get_optimized_image_url(image_path, format='auto'):
    """Convenience function to get optimized image URL"""
    return cdn_manager.get_optimized_image_url(image_path, format) 