#!/usr/bin/env python3
"""
Script de build automatisé pour Vidé-Grenier Kamer
"""

import subprocess
import sys
import os

def run_command(command, description):
    print(f"\n🔄 {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} réussi")
        return True
    else:
        print(f"❌ {description} échoué: {result.stderr}")
        return False

def main():
    print("🚀 Build Vidé-Grenier Kamer")
    print("=" * 40)
    
    # Build Tailwind CSS
    if os.path.exists('package.json'):
        if not run_command('npm run build-css-prod', 'Build Tailwind CSS'):
            print("⚠️  Utilisation du fallback CSS")
    
    # Collecte des fichiers statiques
    run_command('python manage.py collectstatic --noinput', 'Collecte des fichiers statiques')
    
    # Compression des assets (optionnel)
    if run_command('python -c "import gzip"', 'Test compression'):
        run_command('find staticfiles -name "*.css" -exec gzip -k {} \;', 'Compression CSS')
        run_command('find staticfiles -name "*.js" -exec gzip -k {} \;', 'Compression JS')
    
    print("\n🎉 Build terminé!")

if __name__ == "__main__":
    main()
