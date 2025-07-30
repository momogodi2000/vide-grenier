#!/usr/bin/env python3
"""
APK Generation Script for Vidé-Grenier Kamer PWA
This script generates an APK file for the PWA using Buildozer or alternative methods.
"""

import subprocess
import os
import sys
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apk_generation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class APKGenerator:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / 'build'
        self.output_dir = self.project_dir / 'bin'
        self.buildozer_spec = self.project_dir / 'buildozer.spec'
        self.kivy_dir = self.project_dir / 'kivy_app'
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        dependencies = {
            'buildozer': ['buildozer', '--version'],
            'python': ['python', '--version'],
            'git': ['git', '--version']
        }
        
        missing = []
        for dep, command in dependencies.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                logger.info(f"[OK] {dep}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try alternative paths for buildozer
                if dep == 'buildozer':
                    try:
                        # Try common installation paths
                        alt_paths = [
                            'C:\\Users\\momo\\AppData\\Roaming\\Python\\Python313\\Scripts\\buildozer.exe',
                            'C:\\Users\\momo\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\buildozer.exe',
                            'C:\\Python313\\Scripts\\buildozer.exe'
                        ]
                        for alt_path in alt_paths:
                            if os.path.exists(alt_path):
                                result = subprocess.run([alt_path, '--version'], capture_output=True, text=True, check=True)
                                logger.info(f"[OK] {dep}: {result.stdout.strip()} (found at {alt_path})")
                                # Store the path for later use
                                self.buildozer_path = alt_path
                                break
                        else:
                            logger.warning(f"[MISSING] {dep} not found")
                            missing.append(dep)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        logger.warning(f"[MISSING] {dep} not found")
                        missing.append(dep)
                else:
                    logger.warning(f"[MISSING] {dep} not found")
                    missing.append(dep)
        
        if missing:
            logger.error(f"Missing dependencies: {', '.join(missing)}")
            logger.info("Please install missing dependencies:")
            logger.info("pip install buildozer")
            return False
        
        return True
    
    def create_buildozer_spec(self):
        """Create or update buildozer.spec file."""
        spec_content = f"""[app]
title = Vidé-Grenier Kamer
package.name = vgk
package.domain = com.videgrenier.kamer
source.dir = {self.kivy_dir}
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js
version = 1.0.0

requirements = python3,kivy,requests,urllib3

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 28
android.minapi = 21
android.ndk = 23b
android.sdk = 28
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
"""
        
        try:
            with open(self.buildozer_spec, 'w') as f:
                f.write(spec_content)
            logger.info("✓ buildozer.spec created/updated")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create buildozer.spec: {e}")
            return False
    
    def create_kivy_app(self):
        """Create a basic Kivy app wrapper for the PWA."""
        if not self.kivy_dir.exists():
            self.kivy_dir.mkdir()
        
        # Main app file
        main_py = self.kivy_dir / 'main.py'
        main_content = '''import kivy
from kivy.app import App
from kivy.uix.webview import WebView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.utils import platform

class VGKApp(App):
    def build(self):
        # Set window size for desktop testing
        if platform == 'desktop':
            Window.size = (400, 700)
        
        layout = BoxLayout(orientation='vertical')
        
        # Create WebView to load the PWA
        webview = WebView(url='http://localhost:8000')
        layout.add_widget(webview)
        
        return layout

if __name__ == '__main__':
    VGKApp().run()
'''
        
        try:
            with open(main_py, 'w') as f:
                f.write(main_content)
            logger.info("✓ Kivy app created")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create Kivy app: {e}")
            return False
    
    def generate_apk(self, build_type='debug'):
        """
        Generate APK using Buildozer.
        
        Args:
            build_type (str): 'debug' or 'release'
        
        Returns:
            str: Path to generated APK file
        """
        if not self.check_dependencies():
            raise Exception("Missing required dependencies")
        
        if not self.create_buildozer_spec():
            raise Exception("Failed to create buildozer.spec")
        
        if not self.create_kivy_app():
            raise Exception("Failed to create Kivy app")
        
        logger.info(f"Starting APK generation ({build_type})...")
        
        try:
            # Clean previous builds
            if (self.build_dir / 'android').exists():
                shutil.rmtree(self.build_dir / 'android')
            
            # Run buildozer command
            buildozer_cmd = getattr(self, 'buildozer_path', 'buildozer')
            command = [buildozer_cmd, 'android', build_type]
            
            logger.info(f"Running: {' '.join(command)}")
            process = subprocess.run(
                command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if process.returncode != 0:
                logger.error(f"Buildozer failed with return code {process.returncode}")
                logger.error(f"STDOUT: {process.stdout}")
                logger.error(f"STDERR: {process.stderr}")
                raise Exception(f"Buildozer failed: {process.stderr}")
            
            logger.info("Buildozer output:")
            logger.info(process.stdout)
            
            if process.stderr:
                logger.warning("Buildozer warnings:")
                logger.warning(process.stderr)
            
            # Find generated APK
            apk_files = list(self.output_dir.glob('*.apk'))
            if not apk_files:
                # Check build directory
                apk_files = list(self.build_dir.glob('**/*.apk'))
            
            if apk_files:
                # Get the most recent APK
                latest_apk = max(apk_files, key=lambda f: f.stat().st_mtime)
                apk_size = latest_apk.stat().st_size / (1024 * 1024)  # MB
                
                logger.info(f"✓ APK generated successfully: {latest_apk}")
                logger.info(f"✓ APK size: {apk_size:.2f} MB")
                
                return str(latest_apk)
            else:
                raise Exception("No APK file found after build")
                
        except subprocess.TimeoutExpired:
            logger.error("APK generation timed out after 30 minutes")
            raise Exception("APK generation timed out")
        except Exception as e:
            logger.error(f"APK generation failed: {e}")
            raise
    
    def generate_alternative_apk(self):
        """
        Alternative APK generation using PWA Builder or similar tools.
        This is a fallback method when Buildozer is not available.
        """
        logger.info("Attempting alternative APK generation...")
        
        # This would integrate with PWA Builder API or similar service
        # For now, we'll create a placeholder
        logger.warning("Alternative APK generation not implemented yet")
        logger.info("Please install Buildozer for APK generation")
        
        return None

def generate_apk(build_type='debug'):
    """
    Main function to generate APK.
    
    Args:
        build_type (str): 'debug' or 'release'
    
    Returns:
        str: Path to generated APK file
    """
    generator = APKGenerator()
    
    try:
        return generator.generate_apk(build_type)
    except Exception as e:
        logger.error(f"Primary APK generation failed: {e}")
        
        # Try alternative method
        try:
            return generator.generate_alternative_apk()
        except Exception as alt_e:
            logger.error(f"Alternative APK generation also failed: {alt_e}")
            raise Exception(f"All APK generation methods failed: {e}")

def get_apk_info(apk_path):
    """Get information about the generated APK."""
    if not os.path.exists(apk_path):
        return None
    
    stat = os.stat(apk_path)
    return {
        'path': apk_path,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

if __name__ == '__main__':
    try:
        apk_file = generate_apk('debug')
        info = get_apk_info(apk_file)
        
        print("=" * 50)
        print("APK Generation Successful!")
        print("=" * 50)
        print(f"File: {info['path']}")
        print(f"Size: {info['size_mb']} MB")
        print(f"Created: {info['created']}")
        print("=" * 50)
        
    except Exception as e:
        print(f"Failed to generate APK: {e}")
        sys.exit(1) 