#!/usr/bin/env python3
"""
Script de développement pour Vidé-Grenier Kamer
Lance Tailwind en mode watch et le serveur Django optimisé
"""

import subprocess
import sys
import os
import threading
import time
import socket

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_tailwind_watch():
    """Lance Tailwind en mode watch"""
    if os.path.exists('package.json'):
        print("🎨 Démarrage de Tailwind en mode watch...")
        subprocess.run(['npm', 'run', 'dev'], cwd='.')
    else:
        print("⚠️  package.json non trouvé, Tailwind watch non disponible")

def run_django_server(use_plus=True, port=8000):
    """Lance le serveur Django optimisé"""
    if use_plus:
        print("🚀 Démarrage du serveur Django avec runserver_plus (auto-reload optimisé)...")
        cmd = ['python', 'manage.py', 'runserver_plus', f'0.0.0.0:{port}', '--threaded']
    else:
        print("🚀 Démarrage du serveur Django standard...")
        cmd = ['python', 'manage.py', 'runserver', f'0.0.0.0:{port}']
    
    # Force the environment to use development settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'vide.settings.development'
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur de développement")
        sys.exit(0)

def main():
    print("🔧 Mode Développement - Vidé-Grenier Kamer")
    print("=" * 60)
    print("🔄 Optimisation du rechargement automatique activée")
    print("🌐 Django Browser Reload configuré")
    print("🐞 Django Debug Toolbar disponible sur /__debug__/")
    print("=" * 60)
    
    # Vérifier si le port 8000 est déjà utilisé
    port = 8000
    if is_port_in_use(port):
        port = 8001
        print(f"⚠️  Le port 8000 est occupé, utilisation du port {port}")
    
    # Lancer Tailwind en arrière-plan
    tailwind_thread = threading.Thread(target=run_tailwind_watch)
    tailwind_thread.daemon = True
    tailwind_thread.start()
    
    # Petite pause pour laisser Tailwind démarrer
    time.sleep(1.5)
    
    # Tenter de lancer avec runserver_plus, revenir à runserver si non disponible
    try:
        run_django_server(use_plus=True, port=port)
    except Exception as e:
        print(f"⚠️  Erreur avec runserver_plus: {e}")
        print("🔄 Retour au serveur standard...")
        run_django_server(use_plus=False, port=port)

if __name__ == "__main__":
    main()
