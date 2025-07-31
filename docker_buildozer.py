#!/usr/bin/env python3
"""
Docker-based APK generation for Windows
"""

import subprocess
import sys
import os
from pathlib import Path

def check_docker():
    """Check if Docker is installed and running"""
    print("🔍 Checking Docker installation...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker Desktop for Windows.")
        return False
    except subprocess.CalledProcessError:
        print("❌ Docker not running. Please start Docker Desktop.")
        return False

def pull_buildozer_image():
    """Pull the official buildozer Docker image"""
    print("\n📦 Pulling buildozer Docker image...")
    
    try:
        result = subprocess.run(['docker', 'pull', 'kivy/buildozer'], 
                              capture_output=True, text=True, check=True)
        print("✅ Buildozer Docker image pulled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to pull Docker image: {e}")
        return False

def build_apk_with_docker(debug=True):
    """Build APK using Docker"""
    print(f"\n🔨 Building APK with Docker (debug={debug})...")
    
    # Get current directory
    current_dir = os.getcwd()
    
    # Build command
    build_type = "debug" if debug else "release"
    cmd = [
        'docker', 'run', '--rm',
        '--volume', f"{current_dir}:/home/user/hostcwd",
        'kivy/buildozer',
        '--workdir', '/home/user/hostcwd',
        'android', build_type
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print("✅ Docker build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        return False

def setup_docker_environment():
    """Setup Docker environment for buildozer"""
    print("\n🔧 Setting up Docker environment...")
    
    # Create .buildozer directory if it doesn't exist
    buildozer_dir = Path(".buildozer")
    buildozer_dir.mkdir(exist_ok=True)
    
    # Ensure buildozer.spec exists
    spec_file = Path("buildozer.spec")
    if not spec_file.exists():
        print("❌ buildozer.spec not found. Please run buildozer init first.")
        return False
    
    print("✅ Docker environment ready")
    return True

def main():
    """Main Docker build function"""
    print("🚀 Docker-based APK Generation")
    print("="*50)
    
    # Check Docker
    if not check_docker():
        print("\n💡 Please install Docker Desktop for Windows:")
        print("   https://www.docker.com/products/docker-desktop/")
        return False
    
    # Pull Docker image
    if not pull_buildozer_image():
        return False
    
    # Setup environment
    if not setup_docker_environment():
        return False
    
    # Build debug APK
    print("\n🔨 Building debug APK...")
    if build_apk_with_docker(debug=True):
        print("✅ Debug APK build successful")
    else:
        print("❌ Debug APK build failed")
        return False
    
    # Build release APK
    print("\n🔨 Building release APK...")
    if build_apk_with_docker(debug=False):
        print("✅ Release APK build successful")
    else:
        print("❌ Release APK build failed")
        return False
    
    print("\n" + "="*50)
    print("✅ All Docker builds completed!")
    print("\n📱 APK files should be in the 'bin' directory")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 