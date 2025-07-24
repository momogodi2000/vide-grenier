#!/usr/bin/env python3
"""
Install Live Reload Packages for Vidé-Grenier Kamer
This script installs just the packages needed for optimized live reloading.
"""

import subprocess
import sys
import os

def print_header(message):
    print("\n" + "=" * 80)
    print(f"🔄 {message}")
    print("=" * 80)

def main():
    print_header("Installing Django Live Reload Packages")
    
    # Essential packages for live reloading
    packages = [
        "django-browser-reload>=1.12.0",
        "django-debug-toolbar>=4.2.0",
        "django-extensions>=3.2.0",
        "Werkzeug>=3.0.0",
        "watchdog>=3.0.0",
    ]
    
    print("Installing the following packages:")
    for pkg in packages:
        print(f"  - {pkg}")
    
    print("\nRunning pip install...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)
        print("\n✅ Successfully installed live reload packages!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing packages: {e}")
        return 1
    
    print_header("Next Steps")
    print("1. Ensure your development settings are configured correctly")
    print("2. Run the development server with: python dev.py")
    print("3. Access your site at http://localhost:8000")
    print("\nYour site will now automatically reload when changes are detected!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 