#!/usr/bin/env python3
"""
Script pour réparer les problèmes de dépendances du projet Vidé-Grenier Kamer
"""

import os
import sys
import subprocess
import platform

def run_command(command, description=""):
    """Exécute une commande et affiche les résultats"""
    print(f"\n🔄 {description}")
    print(f"Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Succès!")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ Erreur (code {result.returncode})")
            if result.stderr:
                print(f"Erreur: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_virtual_env():
    """Vérifie si nous sommes dans un environnement virtuel"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def main():
    print("🚀 Script de réparation - Vidé-Grenier Kamer")
    print("=" * 50)
    
    # Vérification de l'environnement virtuel
    if not check_virtual_env():
        print("⚠️  Il est recommandé d'utiliser un environnement virtuel")
        response = input("Voulez-vous continuer quand même? (y/N): ")
        if response.lower() != 'y':
            return
    
    print(f"🐍 Python version: {sys.version}")
    print(f"💻 Plateforme: {platform.platform()}")
    
    # Étape 1: Désinstaller les packages problématiques
    print("\n🧹 Nettoyage des packages problématiques...")
    packages_to_remove = ["decouple", "python-decouple"]
    for package in packages_to_remove:
        run_command(f"pip uninstall {package} -y", f"Désinstallation de {package}")
    
    # Étape 2: Mettre à jour pip
    run_command("python -m pip install --upgrade pip", "Mise à jour de pip")
    
    # Étape 3: Nettoyer le cache pip
    run_command("pip cache purge", "Nettoyage du cache pip")
    
    # Étape 4: Installer python-decouple
    run_command("pip install python-decouple==3.8", "Installation de python-decouple")
    
    # Étape 5: Installer les autres dépendances principales
    dependencies = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "psycopg2-binary==2.9.7",
        "whitenoise==6.6.0",
        "django-allauth==0.57.0",
        "django-cors-headers==4.3.1",
        "Pillow==10.0.1"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installation de {dep}")
    
    # Étape 6: Créer le fichier .env s'il n'existe pas
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"\n📝 Création du fichier {env_path}")
        env_content = """# .env - Fichier de configuration local
SECRET_KEY=django-insecure-change-me-in-production-very-long-secret-key-here
DEBUG=True
DJANGO_ENVIRONMENT=development
DATABASE_URL=sqlite:///db.sqlite3
"""
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Fichier .env créé")
    
    # Étape 7: Tester l'import
    print("\n🧪 Test de l'import...")
    try:
        from decouple import config
        print("✅ Import de 'config' depuis 'decouple' réussi!")
        
        # Test avec une valeur par défaut
        test_value = config('SECRET_KEY', default='test')
        print(f"✅ Test de configuration réussi: {test_value[:20]}...")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Étape 8: Vérifier Django
    print("\n🔧 Vérification de Django...")
    if run_command("python -c \"import django; print('Django version:', django.get_version())\"", "Test Django"):
        print("✅ Django fonctionne correctement")
    
    # Étape 9: Test des commandes Django
    print("\n⚙️  Test des commandes Django...")
    os.chdir("vide")  # Se déplacer dans le dossier du projet Django
    
    if run_command("python manage.py check", "Vérification du projet Django"):
        print("✅ Configuration Django valide")
        
        # Essayer collectstatic
        run_command("python manage.py collectstatic --noinput", "Collection des fichiers statiques")
        
        # Essayer les migrations
        run_command("python manage.py makemigrations", "Création des migrations")
        run_command("python manage.py migrate", "Application des migrations")
    
    print("\n🎉 Script de réparation terminé!")
    print("\n📋 Prochaines étapes:")
    print("1. Vérifiez que le serveur démarre: python manage.py runserver")
    print("2. Si il y a encore des erreurs, vérifiez le fichier .env")
    print("3. Assurez-vous d'être dans le bon répertoire (vide/)")

if __name__ == "__main__":
    main()