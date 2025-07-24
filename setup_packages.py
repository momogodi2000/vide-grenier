#!/usr/bin/env python3
"""
Package Installation Script for Vidé-Grenier Kamer
This script installs all necessary packages to run the application.
"""

import subprocess
import sys
import os
import platform
import time

# Core packages required for the app to run
CORE_PACKAGES = [
    "Django==4.2.7",
    "djangorestframework==3.14.0",
    "django-cors-headers==4.3.1",
    "django-filter==23.3",
    "django-allauth==0.57.0",
    "django-crispy-forms==2.1",
    "crispy-bootstrap5==0.7",
    "whitenoise==6.6.0",
    "python-decouple==3.8",
    "Pillow==10.1.0",
    "channels==4.0.0",
]

# Development packages for optimized reloading
DEV_PACKAGES = [
    "django-debug-toolbar==4.2.0",
    "django-extensions==3.2.3",
    "django-browser-reload==1.12.1",
    "Werkzeug==3.0.1",
    "watchdog==3.0.0",
]

def print_header(message):
    print("\n" + "=" * 80)
    print(f"{message}")
    print("=" * 80)

def install_packages(package_list, purpose):
    print_header(f"Installing {purpose} packages")
    
    print(f"Installing {len(package_list)} packages...")
    for i, package in enumerate(package_list, 1):
        print(f"[{i}/{len(package_list)}] Installing {package}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {package}")
    
    print(f"\n✅ Completed installation of {purpose} packages!")

def main():
    print_header("Vidé-Grenier Kamer - Package Installation")
    
    print("This script will install all necessary packages for the Vidé-Grenier Kamer application.")
    print("1. Core packages required for the application")
    print("2. Development packages for optimized live reloading\n")
    
    choice = input("Install (1) Core packages, (2) Dev packages, or (3) Both? [3]: ")
    choice = choice.strip() or "3"
    
    start_time = time.time()
    
    if choice in ["1", "3"]:
        install_packages(CORE_PACKAGES, "core")
    
    if choice in ["2", "3"]:
        install_packages(DEV_PACKAGES, "development")
    
    elapsed_time = time.time() - start_time
    
    print_header("Installation Summary")
    print(f"✅ Installation completed in {elapsed_time:.1f} seconds")
    print("\nTo run the application with optimized live reload:")
    print("1. Start the development server: python dev.py")
    print("2. Access the site at http://localhost:8000")

if __name__ == "__main__":
    main() 