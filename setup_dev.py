#!/usr/bin/env python3
"""
Setup Development Environment for Vidé-Grenier Kamer
This script will install all necessary packages and set up the development environment.
"""

import os
import subprocess
import sys
import platform
import time

def print_status(message):
    """Print a status message with formatting"""
    width = 80
    print("\n" + "=" * width)
    print(f"🔧 {message}")
    print("=" * width)

def check_requirements():
    """Check if Python, pip, and npm are available"""
    print_status("Checking system requirements...")
    
    # Check Python version
    python_version = platform.python_version()
    print(f"✅ Python version: {python_version}")
    
    # Check pip installation
    try:
        pip_version = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'], 
            capture_output=True, text=True
        ).stdout.strip()
        print(f"✅ pip installed: {pip_version}")
    except Exception as e:
        print(f"❌ Error checking pip: {e}")
        sys.exit(1)
    
    # Check npm installation
    try:
        npm_version = subprocess.run(
            ['npm', '--version'], 
            capture_output=True, text=True
        ).stdout.strip()
        print(f"✅ npm installed: {npm_version}")
    except Exception:
        print("❌ npm not found. Please install Node.js and npm")
        sys.exit(1)

def install_python_packages():
    """Install required Python packages"""
    print_status("Installing Python dependencies...")
    
    # Create a virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        print("🔄 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    
    # Determine the correct pip command (works on both Windows and Unix)
    if platform.system() == "Windows":
        pip_cmd = [os.path.join("venv", "Scripts", "pip")]
    else:
        pip_cmd = [os.path.join("venv", "bin", "pip")]
    
    # Upgrade pip
    print("🔄 Upgrading pip...")
    subprocess.run(pip_cmd + ["install", "--upgrade", "pip"])
    
    # Install development packages
    print("🔄 Installing development packages...")
    subprocess.run(pip_cmd + ["install", "-r", "requirements-dev.txt"])
    
    print("✅ Python packages installed successfully!")

def setup_npm_packages():
    """Install and build npm packages"""
    print_status("Setting up npm packages...")
    
    # Install npm packages
    subprocess.run(["npm", "install"])
    
    # Build Tailwind CSS
    subprocess.run(["npm", "run", "build"])
    
    print("✅ npm packages installed successfully!")

def configure_environment():
    """Set up environment configuration"""
    print_status("Configuring environment...")
    
    # Check if .env file exists, if not create from example
    if not os.path.exists('.env') and os.path.exists('env_config.example'):
        print("🔄 Creating .env file from template...")
        with open('env_config.example', 'r') as f:
            env_template = f.read()
        
        with open('.env', 'w') as f:
            f.write(env_template)
        
        print("✅ Created .env file (please update settings if needed)")
    else:
        print("✅ .env file already exists")

def run_migrations():
    """Run Django migrations"""
    print_status("Running database migrations...")
    
    # Determine the correct python command
    if platform.system() == "Windows":
        python_cmd = os.path.join("venv", "Scripts", "python")
    else:
        python_cmd = os.path.join("venv", "bin", "python")
    
    # Make migrations
    print("🔄 Creating migrations...")
    subprocess.run([python_cmd, "manage.py", "makemigrations"])
    
    # Apply migrations
    print("🔄 Applying migrations...")
    subprocess.run([python_cmd, "manage.py", "migrate"])
    
    print("✅ Database migrations complete!")

def main():
    """Main function to set up the development environment"""
    start_time = time.time()
    
    print("\n" + "=" * 80)
    print("🚀 Setting up Vidé-Grenier Kamer Development Environment 🚀")
    print("=" * 80)
    
    # Run all setup steps
    check_requirements()
    install_python_packages()
    setup_npm_packages()
    configure_environment()
    run_migrations()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"✨ Setup Complete! (Completed in {elapsed_time:.2f} seconds)")
    print("=" * 80)
    print("\nTo start the development server:")
    print("1. Activate your virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Run the development server:")
    print("   python dev.py")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main() 