#!/usr/bin/env python3
"""
Enhanced APK Building Script for Vidé-Grenier Kamer
Supports multiple store deployments and signing options
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APKBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / 'build'
        self.output_dir = self.project_dir / 'bin'
        self.keystore_path = self.project_dir / 'vgk-release-key.keystore'
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def check_dependencies(self):
        """Check if required tools are installed"""
        tools = {
            'buildozer': 'buildozer --version',
            'keytool': 'keytool -help',
            'jarsigner': 'jarsigner -help',
            'zipalign': 'zipalign -help'
        }
        
        missing = []
        for tool, command in tools.items():
            try:
                subprocess.run(command.split(), capture_output=True, check=True)
                logger.info(f"✓ {tool} found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(f"✗ {tool} not found")
                missing.append(tool)
        
        return missing
    
    def generate_keystore(self, force=False):
        """Generate keystore for signing"""
        if self.keystore_path.exists() and not force:
            logger.info("Keystore already exists. Use --force to regenerate.")
            return True
        
        logger.info("Generating keystore for APK signing...")
        
        cmd = [
            'keytool', '-genkey', '-v',
            '-keystore', str(self.keystore_path),
            '-alias', 'vgk-key-alias',
            '-keyalg', 'RSA',
            '-keysize', '2048',
            '-validity', '10000',
            '-storepass', 'vgk123456',
            '-keypass', 'vgk123456',
            '-dname', 'CN=VGK, OU=Development, O=Vide-Grenier Kamer, L=Douala, S=Douala, C=CM'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info("✓ Keystore generated successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to generate keystore: {e}")
            return False
    
    def build_apk(self, build_type='debug', store=None):
        """Build APK with specific configuration"""
        logger.info(f"Building {build_type} APK for {store or 'general'}...")
        
        # Create buildozer spec with store-specific settings
        spec_content = self._create_buildozer_spec(build_type, store)
        
        with open(self.project_dir / 'buildozer.spec', 'w') as f:
            f.write(spec_content)
        
        # Build APK
        cmd = ['buildozer', 'android', build_type]
        
        try:
            subprocess.run(cmd, cwd=self.project_dir, check=True)
            logger.info("✓ APK built successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ APK build failed: {e}")
            return False
    
    def _create_buildozer_spec(self, build_type, store):
        """Create buildozer.spec with store-specific settings"""
        base_spec = f"""[app]
title = Vidé-Grenier Kamer
package.name = vgk
package.domain = com.videgrenier.kamer
source.dir = kivy_app
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
"""
        
        # Store-specific configurations
        if store == 'google':
            base_spec += """
# Google Play Store specific
android.target_sdk = 33
android.allow_backup = True
android.usesCleartextTraffic = False
"""
        elif store == 'huawei':
            base_spec += """
# Huawei AppGallery specific
android.target_sdk = 30
android.allow_backup = True
android.usesCleartextTraffic = True
android.huawei = True
"""
        elif store == 'samsung':
            base_spec += """
# Samsung Galaxy Store specific
android.target_sdk = 31
android.allow_backup = True
android.usesCleartextTraffic = False
android.samsung = True
"""
        
        base_spec += """
[buildozer]
log_level = 2
warn_on_root = 1
"""
        
        return base_spec
    
    def sign_apk(self, apk_path, output_path=None):
        """Sign APK for release"""
        if not self.keystore_path.exists():
            logger.error("Keystore not found. Generate it first.")
            return False
        
        if output_path is None:
            output_path = apk_path.replace('-unsigned', '-signed')
        
        logger.info("Signing APK...")
        
        # Sign APK
        sign_cmd = [
            'jarsigner', '-verbose', '-sigalg', 'SHA1withRSA',
            '-digestalg', 'SHA1', '-keystore', str(self.keystore_path),
            apk_path, 'vgk-key-alias', '-storepass', 'vgk123456'
        ]
        
        try:
            subprocess.run(sign_cmd, check=True)
            logger.info("✓ APK signed successfully")
            
            # Optimize APK
            optimize_cmd = ['zipalign', '-v', '4', apk_path, output_path]
            subprocess.run(optimize_cmd, check=True)
            logger.info("✓ APK optimized successfully")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ APK signing failed: {e}")
            return False
    
    def find_apk(self, build_type='debug'):
        """Find generated APK file"""
        apk_pattern = f"*{build_type}*.apk"
        apk_files = list(self.output_dir.glob(apk_pattern))
        
        if not apk_files:
            # Check build directory
            apk_files = list(self.build_dir.glob(f"**/{apk_pattern}"))
        
        if apk_files:
            return max(apk_files, key=lambda f: f.stat().st_mtime)
        return None
    
    def build_for_store(self, store, build_type='release'):
        """Build APK optimized for specific store"""
        logger.info(f"Building APK for {store} store...")
        
        # Build APK
        if not self.build_apk(build_type, store):
            return None
        
        # Find APK
        apk_path = self.find_apk(build_type)
        if not apk_path:
            logger.error("APK not found after build")
            return None
        
        # Sign APK for release
        if build_type == 'release':
            signed_apk = apk_path.parent / f"vgk-{store}-release.apk"
            if not self.sign_apk(str(apk_path), str(signed_apk)):
                return None
            return signed_apk
        
        return apk_path

def main():
    parser = argparse.ArgumentParser(description='Build APK for Vidé-Grenier Kamer')
    parser.add_argument('--type', choices=['debug', 'release'], default='debug',
                       help='Build type (debug or release)')
    parser.add_argument('--store', choices=['google', 'huawei', 'samsung'],
                       help='Target store for optimization')
    parser.add_argument('--keystore', action='store_true',
                       help='Generate keystore for signing')
    parser.add_argument('--force', action='store_true',
                       help='Force regenerate keystore')
    parser.add_argument('--sign', action='store_true',
                       help='Sign APK after building')
    
    args = parser.parse_args()
    
    builder = APKBuilder()
    
    # Check dependencies
    missing = builder.check_dependencies()
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.info("Please install missing tools before continuing.")
        return 1
    
    # Generate keystore if requested
    if args.keystore or args.store:
        if not builder.generate_keystore(args.force):
            return 1
    
    # Build APK
    if args.store:
        apk_path = builder.build_for_store(args.store, args.type)
    else:
        if not builder.build_apk(args.type):
            return 1
        apk_path = builder.find_apk(args.type)
    
    if not apk_path:
        logger.error("APK not found")
        return 1
    
    # Sign APK if requested
    if args.sign and args.type == 'release':
        signed_apk = apk_path.parent / f"vgk-signed-release.apk"
        if not builder.sign_apk(str(apk_path), str(signed_apk)):
            return 1
        apk_path = signed_apk
    
    # Display results
    apk_size = apk_path.stat().st_size / (1024 * 1024)
    logger.info("=" * 50)
    logger.info("APK Build Successful!")
    logger.info("=" * 50)
    logger.info(f"File: {apk_path}")
    logger.info(f"Size: {apk_size:.2f} MB")
    logger.info(f"Type: {args.type}")
    if args.store:
        logger.info(f"Store: {args.store}")
    logger.info("=" * 50)
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 