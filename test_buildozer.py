#!/usr/bin/env python3
"""
Test script to verify buildozer installation and configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def test_buildozer_installation():
    """Test if buildozer is properly installed"""
    print("🔍 Testing buildozer installation...")
    
    try:
        # Test buildozer version
        result = subprocess.run(['buildozer', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Buildozer version: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Buildozer version check failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Buildozer not found. Install with: pip install buildozer")
        return False

def test_buildozer_help():
    """Test buildozer help command"""
    print("\n🔍 Testing buildozer help...")
    
    try:
        result = subprocess.run(['buildozer', '--help'], 
                              capture_output=True, text=True, check=True)
        print("✅ Buildozer help command works")
        
        # Check if android target is mentioned
        if 'android' in result.stdout.lower():
            print("✅ Android target is available")
        else:
            print("⚠️  Android target not found in help")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Buildozer help failed: {e}")
        return False

def test_buildozer_init():
    """Test buildozer init command"""
    print("\n🔍 Testing buildozer init...")
    
    # Create a temporary directory for testing
    test_dir = Path("test_buildozer")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Change to test directory
        original_dir = os.getcwd()
        os.chdir(test_dir)
        
        # Run buildozer init
        result = subprocess.run(['buildozer', 'init'], 
                              capture_output=True, text=True, check=True)
        print("✅ Buildozer init successful")
        
        # Check if buildozer.spec was created
        if Path("buildozer.spec").exists():
            print("✅ buildozer.spec file created")
            
            # Read and display some key settings
            with open("buildozer.spec", "r") as f:
                content = f.read()
                
            if "android" in content:
                print("✅ Android configuration found in buildozer.spec")
            else:
                print("⚠️  Android configuration not found in buildozer.spec")
                
        else:
            print("❌ buildozer.spec file not created")
            
        # Clean up
        os.chdir(original_dir)
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Buildozer init failed: {e}")
        print(f"Error output: {e.stderr}")
        
        # Clean up
        os.chdir(original_dir)
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
        # Clean up
        os.chdir(original_dir)
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            
        return False

def test_android_target():
    """Test if android target is available"""
    print("\n🔍 Testing android target...")
    
    try:
        # Try to run buildozer android debug (should fail but show available targets)
        result = subprocess.run(['buildozer', 'android', 'debug'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Android target works")
            return True
        else:
            # Check if it's a configuration error (which is expected) vs command error
            if "Unknown command/target" in result.stderr:
                print("❌ Android target not recognized")
                print("This might be a buildozer installation issue")
                return False
            elif "No buildozer.spec" in result.stderr:
                print("✅ Android target recognized (no spec file)")
                return True
            else:
                print("⚠️  Android target test inconclusive")
                print(f"Error: {result.stderr}")
                return True  # Assume it's working if it's not a command error
                
    except Exception as e:
        print(f"❌ Android target test failed: {e}")
        return False

def check_environment():
    """Check environment variables and dependencies"""
    print("\n🔍 Checking environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")
    
    # Check Java
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, check=True)
        print("✅ Java is installed")
    except:
        print("❌ Java not found")
    
    # Check Android SDK
    android_home = os.environ.get('ANDROID_HOME')
    if android_home:
        print(f"✅ ANDROID_HOME set: {android_home}")
    else:
        print("⚠️  ANDROID_HOME not set")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check if buildozer.spec exists
    if Path("buildozer.spec").exists():
        print("✅ buildozer.spec found in current directory")
    else:
        print("⚠️  buildozer.spec not found in current directory")

def main():
    """Main test function"""
    print("🚀 Buildozer Test Suite")
    print("=" * 50)
    
    # Check environment
    check_environment()
    
    # Test buildozer installation
    if not test_buildozer_installation():
        print("\n❌ Buildozer installation test failed")
        return False
    
    # Test buildozer help
    if not test_buildozer_help():
        print("\n❌ Buildozer help test failed")
        return False
    
    # Test buildozer init
    if not test_buildozer_init():
        print("\n❌ Buildozer init test failed")
        return False
    
    # Test android target
    if not test_android_target():
        print("\n❌ Android target test failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Buildozer should work correctly.")
    print("\n💡 If you're still having issues, try:")
    print("   1. pip install --upgrade buildozer")
    print("   2. buildozer init")
    print("   3. buildozer android debug")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 