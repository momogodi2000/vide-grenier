#!/usr/bin/env python3
"""
Script de développement pour Vidé-Grenier Kamer
Lance Tailwind en mode watch et le serveur Django
"""

import subprocess
import sys
import os
import threading
import time

def run_tailwind_watch():
    """Lance Tailwind en mode watch"""
    if os.path.exists('package.json'):
        print("🎨 Démarrage de Tailwind en mode watch...")
        subprocess.run(['npm', 'run', 'dev'], cwd='.')
    else:
        print("⚠️  package.json non trouvé, Tailwind watch non disponible")

def run_django_server():
    """Lance le serveur Django"""
    print("🚀 Démarrage du serveur Django...")
    time.sleep(2)  # Attendre un peu pour que Tailwind démarre
    subprocess.run(['python', 'manage.py', 'runserver'])

def main():
    print("🔧 Mode Développement - Vidé-Grenier Kamer")
    print("=" * 45)
    
    # Lancer Tailwind en arrière-plan
    tailwind_thread = threading.Thread(target=run_tailwind_watch)
    tailwind_thread.daemon = True
    tailwind_thread.start()
    
    # Lancer Django
    try:
        run_django_server()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur de développement")
        sys.exit(0)

if __name__ == "__main__":
    main()
