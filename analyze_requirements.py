#!/usr/bin/env python3
"""
Analyze requirements.txt and generate an optimized pip install command
for the Vidé-Grenier Kamer application.
"""

import os
import re
import sys
import platform
import subprocess

# Core packages required for the app to function
CORE_PACKAGES = [
    # Django core
    "django>=4.2.7,<5.0",
    "djangorestframework>=3.14.0",
    "django-cors-headers>=4.3.0",
    "django-filter>=23.3",
    
    # Database
    "psycopg2-binary>=2.9.7",
    
    # Cache & Async
    "redis>=5.0.0",
    "django-redis>=5.4.0",
    
    # Authentication
    "django-allauth>=0.57.0",
    "cryptography>=41.0.0",
    "PyJWT>=2.8.0",
    
    # Templating & Frontend
    "whitenoise>=6.6.0",
    "crispy-bootstrap5>=0.7",
    "django-crispy-forms>=2.0",
    
    # Media handling
    "Pillow>=10.0.0",
    
    # Environment & Config
    "python-decouple>=3.8",
    "django-environ>=0.11.0",
    
    # Utilities
    "python-slugify>=8.0.0",
    "pytz>=2023.3",
]

# Development packages for enhanced development experience
DEV_PACKAGES = [
    "django-debug-toolbar>=4.2.0",
    "django-extensions>=3.2.0",
    "django-browser-reload>=1.12.0",
    "Werkzeug>=3.0.0",
    "watchdog>=3.0.0",
    "ipython>=8.0.0",
]

def analyze_requirements_file(file_path):
    """Analyze requirements.txt and extract essential packages"""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract package names and versions using regex
    package_pattern = re.compile(r'^([a-zA-Z0-9_-]+)==([0-9.]+)', re.MULTILINE)
    matches = package_pattern.findall(content)
    
    # Format as package==version
    return [f"{package}=={version}" for package, version in matches]

def check_installed_packages():
    """Check which packages are already installed"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                               capture_output=True, text=True, check=True)
        installed = result.stdout.strip().split('\n')[2:]  # Skip header rows
        
        # Extract package names
        installed_packages = {}
        for pkg in installed:
            parts = pkg.split()
            if len(parts) >= 2:
                installed_packages[parts[0].lower()] = parts[1]
        
        return installed_packages
    except Exception as e:
        print(f"Error checking installed packages: {e}")
        return {}

def generate_install_commands():
    """Generate pip install commands for the application"""
    requirements_file = 'requirements.txt'
    requirements = analyze_requirements_file(requirements_file)
    
    # Check which core packages are in requirements
    core_packages_to_install = []
    for package in CORE_PACKAGES:
        package_name = package.split('>=')[0].split('<')[0].strip()
        found = False
        for req in requirements:
            if req.lower().startswith(package_name.lower() + '=='):
                core_packages_to_install.append(req)
                found = True
                break
        if not found:
            core_packages_to_install.append(package)
    
    # Add development packages
    dev_packages = DEV_PACKAGES
    
    # Generate commands
    core_cmd = f"{sys.executable} -m pip install {' '.join(core_packages_to_install)}"
    dev_cmd = f"{sys.executable} -m pip install {' '.join(dev_packages)}"
    
    return core_cmd, dev_cmd

def main():
    """Main function to analyze requirements and print install commands"""
    print("\n" + "=" * 80)
    print("Vidé-Grenier Kamer - Requirements Analyzer")
    print("=" * 80)
    
    core_cmd, dev_cmd = generate_install_commands()
    
    print("\n1. Core Packages Installation Command:")
    print("-" * 50)
    print(core_cmd)
    
    print("\n2. Development Packages Installation Command:")
    print("-" * 50)
    print(dev_cmd)
    
    print("\n3. Quick Install All Packages:")
    print("-" * 50)
    print("# Core production packages")
    print(core_cmd)
    print("\n# Development packages")
    print(dev_cmd)
    
    print("\n" + "=" * 80)
    print("To optimize Django live reload, run:")
    print("python dev.py")
    print("=" * 80)

if __name__ == "__main__":
    main() 