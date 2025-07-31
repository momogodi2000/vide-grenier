#!/usr/bin/env python3
"""
Enhanced APK Generation Script for Vidé-Grenier Kamer
Supports Android APK/AAB and iOS builds with proper configuration
"""

import os
import sys
import subprocess
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

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
    """Enhanced APK Generator for VGK Mobile App"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.kivy_app_dir = self.project_root / 'kivy_app'
        self.build_dir = self.project_root / 'build'
        self.bin_dir = self.project_root / 'bin'
        self.assets_dir = self.project_root / 'assets'
        
        # App configuration
        self.app_config = {
            'name': 'Vidé-Grenier Kamer',
            'package_name': 'com.videgrenierkamer.app',
            'version': '1.0.0',
            'build_number': '1',
            'min_sdk': 21,
            'target_sdk': 33
        }
        
        # Create necessary directories
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [self.build_dir, self.bin_dir, self.assets_dir]
        for directory in directories:
            directory.mkdir(exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            logger.error("Python 3.8+ is required")
            return False
        
        # Check if buildozer is installed
        try:
            subprocess.run(['buildozer', '--version'], check=True, capture_output=True)
            logger.info("[OK] Buildozer is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("[ERROR] Buildozer is not installed. Install with: pip install buildozer")
            return False
        
        # Check if Android SDK is available (optional for development)
        android_home = os.environ.get('ANDROID_HOME')
        if android_home:
            logger.info(f"[OK] Android SDK found at: {android_home}")
        else:
            logger.warning("[WARNING] Android SDK not found. Buildozer will download it automatically.")
        
        # Check if Java is installed
        try:
            subprocess.run(['java', '-version'], check=True, capture_output=True)
            logger.info("[OK] Java is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("[ERROR] Java is not installed. Install OpenJDK 8 or 11")
            return False
        
        return True
    
    def setup_buildozer_config(self):
        """Setup buildozer configuration"""
        logger.info("Setting up buildozer configuration...")
        
        buildozer_spec = self.project_root / 'buildozer.spec'
        
        # If buildozer.spec doesn't exist, initialize it
        if not buildozer_spec.exists():
            logger.info("Initializing buildozer configuration...")
            try:
                # Change to project directory
                os.chdir(self.project_root)
                
                # Initialize buildozer
                result = subprocess.run(
                    ['buildozer', 'init'],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                logger.info("[OK] Buildozer initialized")
            except subprocess.CalledProcessError as e:
                logger.error(f"[ERROR] Failed to initialize buildozer: {e}")
                return False
        
        # Update buildozer.spec with current configuration
        self.update_buildozer_spec()
        
        logger.info("[OK] Buildozer configuration ready")
        return True
    
    def update_buildozer_spec(self):
        """Update buildozer.spec with current configuration"""
        buildozer_spec_path = self.project_root / 'buildozer.spec'
        
        if not buildozer_spec_path.exists():
            logger.error("buildozer.spec not found")
            return False
        
        # Read current buildozer.spec
        with open(buildozer_spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update version and build number
        content = content.replace('version = 1.0.0', f'version = {self.app_config["version"]}')
        
        # Ensure source.dir points to kivy_app
        content = content.replace('source.dir = .', 'source.dir = kivy_app')
        
        # Update package name
        content = content.replace('package.name = myapp', f'package.name = {self.app_config["package_name"]}')
        
        # Update title
        content = content.replace('title = My Application', f'title = {self.app_config["name"]}')
        
        # Write updated content
        with open(buildozer_spec_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("[OK] Updated buildozer.spec")
    
    def create_app_assets(self):
        """Create app assets (icons, splash screens)"""
        logger.info("Creating app assets...")
        
        # Create app icon if it doesn't exist
        icon_path = self.assets_dir / 'icon.png'
        if not icon_path.exists():
            self.create_default_icon()
        
        # Create splash screen if it doesn't exist
        splash_path = self.assets_dir / 'splash.png'
        if not splash_path.exists():
            self.create_default_splash()
        
        logger.info("[OK] App assets created")
    
    def create_default_icon(self):
        """Create a default app icon"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a 512x512 icon
            size = (512, 512)
            icon = Image.new('RGBA', size, (0, 150, 200, 255))
            draw = ImageDraw.Draw(icon)
            
            # Draw a simple VGK logo
            draw.ellipse([50, 50, 462, 462], fill=(255, 255, 255, 255))
            draw.text((256, 200), "VGK", fill=(0, 150, 200, 255), anchor="mm")
            draw.text((256, 300), "Kamer", fill=(0, 150, 200, 255), anchor="mm")
            
            icon.save(self.assets_dir / 'icon.png')
            logger.info("[OK] Created default app icon")
            
        except ImportError:
            logger.warning("PIL not available, skipping icon creation")
        except Exception as e:
            logger.error(f"Error creating icon: {e}")
    
    def create_default_splash(self):
        """Create a default splash screen"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a 1080x1920 splash screen
            size = (1080, 1920)
            splash = Image.new('RGBA', size, (0, 150, 200, 255))
            draw = ImageDraw.Draw(splash)
            
            # Draw app title
            draw.text((540, 800), "Vidé-Grenier", fill=(255, 255, 255, 255), anchor="mm")
            draw.text((540, 900), "Kamer", fill=(255, 255, 255, 255), anchor="mm")
            draw.text((540, 1000), "Marketplace Camerounais", fill=(255, 255, 255, 255), anchor="mm")
            
            splash.save(self.assets_dir / 'splash.png')
            logger.info("[OK] Created default splash screen")
            
        except ImportError:
            logger.warning("PIL not available, skipping splash creation")
        except Exception as e:
            logger.error(f"Error creating splash: {e}")
    
    def build_android_apk(self, release=False):
        """Build Android APK"""
        logger.info(f"Building Android APK (release={release})...")
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # First, try to clean any previous builds
            try:
                subprocess.run(['buildozer', 'clean'], capture_output=True, text=True, encoding='utf-8')
                logger.info("[OK] Cleaned previous builds")
            except:
                pass
            
            # Build command - use correct buildozer syntax
            if release:
                cmd = ['buildozer', 'android', 'release']
                logger.info("Building release APK...")
            else:
                cmd = ['buildozer', 'android', 'debug']
                logger.info("Building debug APK...")
            
            # Run build command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            logger.info("[OK] Android APK build completed successfully")
            
            # Find the generated APK
            apk_files = list(self.bin_dir.glob('*.apk'))
            if apk_files:
                apk_path = apk_files[0]
                logger.info(f"[OK] APK generated: {apk_path}")
                return str(apk_path)
            else:
                logger.warning("No APK file found in bin directory")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] Android build failed: {e}")
            logger.error(f"Build output: {e.stdout}")
            logger.error(f"Build errors: {e.stderr}")
            
            # Try alternative approach
            logger.info("Trying alternative build approach...")
            return self.try_alternative_build(release)
            
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during Android build: {e}")
            return None
    
    def try_alternative_build(self, release=False):
        """Try alternative build approach"""
        try:
            # Try using buildozer with different syntax
            if release:
                cmd = ['buildozer', '--verbose', 'android', 'release']
            else:
                cmd = ['buildozer', '--verbose', 'android', 'debug']
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            logger.info("[OK] Alternative build successful")
            
            # Find the generated APK
            apk_files = list(self.bin_dir.glob('*.apk'))
            if apk_files:
                apk_path = apk_files[0]
                logger.info(f"[OK] APK generated: {apk_path}")
                return str(apk_path)
            else:
                logger.warning("No APK file found in bin directory")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] Alternative build also failed: {e}")
            logger.error(f"Build output: {e.stdout}")
            logger.error(f"Build errors: {e.stderr}")
            return None
    
    def build_android_aab(self):
        """Build Android App Bundle (AAB)"""
        logger.info("Building Android App Bundle (AAB)...")
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Build AAB command
            cmd = ['buildozer', 'android', 'release']
            
            # Run build command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            logger.info("[OK] Android AAB build completed successfully")
            
            # Find the generated AAB
            aab_files = list(self.bin_dir.glob('*.aab'))
            if aab_files:
                aab_path = aab_files[0]
                logger.info(f"[OK] AAB generated: {aab_path}")
                return str(aab_path)
            else:
                logger.warning("No AAB file found in bin directory")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] Android AAB build failed: {e}")
            logger.error(f"Build output: {e.stdout}")
            logger.error(f"Build errors: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during Android AAB build: {e}")
            return None
    
    def build_ios(self):
        """Build iOS app (requires macOS and Xcode)"""
        logger.info("Building iOS app...")
        
        if sys.platform != 'darwin':
            logger.error("[ERROR] iOS builds require macOS")
            return None
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Build iOS command
            cmd = ['buildozer', 'ios', 'debug']
            
            # Run build command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            logger.info("[OK] iOS build completed successfully")
            
            # Find the generated IPA
            ipa_files = list(self.bin_dir.glob('*.ipa'))
            if ipa_files:
                ipa_path = ipa_files[0]
                logger.info(f"[OK] IPA generated: {ipa_path}")
                return str(ipa_path)
            else:
                logger.warning("No IPA file found in bin directory")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] iOS build failed: {e}")
            logger.error(f"Build output: {e.stdout}")
            logger.error(f"Build errors: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during iOS build: {e}")
            return None
    
    def clean_build(self):
        """Clean build artifacts"""
        logger.info("Cleaning build artifacts...")
        
        try:
            # Remove build directory
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                logger.info("[OK] Removed build directory")
            
            # Remove .buildozer directory
            buildozer_dir = self.project_root / '.buildozer'
            if buildozer_dir.exists():
                shutil.rmtree(buildozer_dir)
                logger.info("[OK] Removed .buildozer directory")
            
            # Remove bin directory contents
            if self.bin_dir.exists():
                for file in self.bin_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                logger.info("[OK] Cleaned bin directory")
            
        except Exception as e:
            logger.error(f"Error cleaning build: {e}")
    
    def generate_build_report(self, build_results):
        """Generate build report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'app_config': self.app_config,
            'build_results': build_results,
            'summary': {
                'total_builds': len(build_results),
                'successful_builds': len([r for r in build_results.values() if r]),
                'failed_builds': len([r for r in build_results.values() if not r])
            }
        }
        
        report_path = self.project_root / 'build_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"[OK] Build report generated: {report_path}")
        return report
    
    def run_full_build(self, platforms=None, clean=False):
        """Run full build process"""
        if platforms is None:
            platforms = ['android_apk', 'android_aab']
        
        logger.info(f"Starting full build process for platforms: {platforms}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites check failed")
            return False
        
        # Setup buildozer
        if not self.setup_buildozer_config():
            logger.error("Buildozer setup failed")
            return False
        
        # Create assets
        self.create_app_assets()
        
        # Clean if requested
        if clean:
            self.clean_build()
        
        # Build results
        build_results = {}
        
        # Build for each platform
        for platform in platforms:
            logger.info(f"Building for {platform}...")
            
            if platform == 'android_apk':
                result = self.build_android_apk(release=False)
                build_results['android_apk_debug'] = result
                
                # Also build release APK
                result_release = self.build_android_apk(release=True)
                build_results['android_apk_release'] = result_release
                
            elif platform == 'android_aab':
                result = self.build_android_aab()
                build_results['android_aab'] = result
                
            elif platform == 'ios':
                result = self.build_ios()
                build_results['ios'] = result
                
            else:
                logger.warning(f"Unknown platform: {platform}")
                build_results[platform] = None
        
        # Generate build report
        report = self.generate_build_report(build_results)
        
        # Print summary
        logger.info("=== BUILD SUMMARY ===")
        logger.info(f"Total builds: {report['summary']['total_builds']}")
        logger.info(f"Successful: {report['summary']['successful_builds']}")
        logger.info(f"Failed: {report['summary']['failed_builds']}")
        
        for platform, result in build_results.items():
            status = "[OK] SUCCESS" if result else "[ERROR] FAILED"
            logger.info(f"{platform}: {status}")
            if result:
                logger.info(f"  Output: {result}")
        
        return report['summary']['successful_builds'] > 0

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate APK/AAB for Vidé-Grenier Kamer')
    parser.add_argument('--platforms', nargs='+', 
                       choices=['android_apk', 'android_aab', 'ios'],
                       default=['android_apk', 'android_aab'],
                       help='Platforms to build for')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build artifacts before building')
    parser.add_argument('--release', action='store_true',
                       help='Build release versions')
    
    args = parser.parse_args()
    
    # Create generator
    generator = APKGenerator()
    
    # Run build
    success = generator.run_full_build(
        platforms=args.platforms,
        clean=args.clean
    )
    
    if success:
        logger.info("🎉 Build process completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Build process failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 