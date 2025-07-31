#!/usr/bin/env python3
"""
Debug script to understand buildozer android target issue
"""

import subprocess
import sys
import os
from pathlib import Path

def debug_buildozer():
    """Debug buildozer installation and configuration"""
    print("🔍 Debugging buildozer...")
    
    # Check buildozer version and help
    try:
        result = subprocess.run(['buildozer', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"Buildozer version: {result.stdout.strip()}")
    except Exception as e:
        print(f"Error getting buildozer version: {e}")
        return
    
    # Check buildozer help
    try:
        result = subprocess.run(['buildozer', '--help'], 
                              capture_output=True, text=True, check=True)
        print(f"\nBuildozer help output:\n{result.stdout}")
    except Exception as e:
        print(f"Error getting buildozer help: {e}")
        return
    
    # Check if buildozer.spec exists and its content
    spec_file = Path("buildozer.spec")
    if spec_file.exists():
        print(f"\n✅ buildozer.spec exists")
        with open(spec_file, 'r') as f:
            content = f.read()
            if 'android' in content.lower():
                print("✅ Android configuration found in buildozer.spec")
            else:
                print("❌ Android configuration NOT found in buildozer.spec")
    else:
        print("❌ buildozer.spec not found")
        return
    
    # Try different buildozer commands
    print("\n🔍 Testing different buildozer commands...")
    
    commands_to_test = [
        ['buildozer', 'android', 'debug'],
        ['buildozer', 'android', 'release'],
        ['buildozer', '--verbose', 'android', 'debug'],
        ['buildozer', '--help'],
        ['buildozer', 'init'],
        ['buildozer', 'clean'],
    ]
    
    for cmd in commands_to_test:
        print(f"\nTesting: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"STDOUT: {result.stdout[:200]}...")
            if result.stderr:
                print(f"STDERR: {result.stderr[:200]}...")
        except Exception as e:
            print(f"Error: {e}")

def check_buildozer_installation():
    """Check buildozer installation details"""
    print("\n🔍 Checking buildozer installation...")
    
    try:
        import buildozer
        print(f"Buildozer module location: {buildozer.__file__}")
        
        # Check if buildozer has android support
        if hasattr(buildozer, 'android'):
            print("✅ Buildozer has android module")
        else:
            print("❌ Buildozer does not have android module")
            
    except ImportError as e:
        print(f"❌ Cannot import buildozer: {e}")
    
    # Check buildozer executable
    try:
        result = subprocess.run(['where', 'buildozer'], 
                              capture_output=True, text=True, check=True)
        print(f"Buildozer executable: {result.stdout.strip()}")
    except:
        print("❌ Cannot find buildozer executable")

def try_manual_buildozer():
    """Try manual buildozer commands"""
    print("\n🔍 Trying manual buildozer commands...")
    
    # First, let's try to clean
    print("1. Cleaning buildozer...")
    try:
        subprocess.run(['buildozer', 'clean'], check=True)
        print("✅ Clean successful")
    except Exception as e:
        print(f"❌ Clean failed: {e}")
    
    # Try to build with more verbose output
    print("\n2. Trying build with verbose output...")
    try:
        result = subprocess.run(['buildozer', '--verbose', 'android', 'debug'], 
                              capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"❌ Build failed: {e}")

def main():
    """Main debug function"""
    print("🚀 Buildozer Debug Tool")
    print("=" * 50)
    
    debug_buildozer()
    check_buildozer_installation()
    try_manual_buildozer()
    
    print("\n" + "=" * 50)
    print("🔍 Debug complete!")

if __name__ == '__main__':
    main() 