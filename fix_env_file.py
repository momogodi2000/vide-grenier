#!/usr/bin/env python3
"""
Script pour réparer le fichier .env avec problème d'encodage
"""

import os
import sys

def fix_env_file():
    """Répare le fichier .env avec le bon encodage"""
    
    env_path = ".env"
    backup_path = ".env.backup"
    
    print("🔧 Réparation du fichier .env...")
    
    # Sauvegarder l'ancien fichier s'il existe
    if os.path.exists(env_path):
        print(f"💾 Sauvegarde de l'ancien fichier vers {backup_path}")
        try:
            os.rename(env_path, backup_path)
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde: {e}")
    
    # Créer un nouveau fichier .env avec le bon encodage
    env_content = """# Configuration Vidé-Grenier Kamer - Développement
# Fichier créé automatiquement avec encodage UTF-8

# Django Core Settings
SECRET_KEY=django-insecure-your-very-long-secret-key-change-me-in-production-123456789
DEBUG=True
DJANGO_ENVIRONMENT=development

# Database Configuration
# Pour le développement, utilise SQLite (pas besoin de configuration)
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (optionnel pour le développement)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment APIs (pour les tests)
CAMPAY_API_KEY=your-campay-api-key-here
NOUPIA_API_KEY=your-noupia-api-key-here
ORANGE_MONEY_API_KEY=your-orange-money-api-key
MTN_MONEY_API_KEY=your-mtn-money-api-key

# Cloud Storage Configuration (Cloudinary)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token

# AWS Configuration (si nécessaire)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=vgk-media-bucket
"""
    
    try:
        # Écrire le nouveau fichier avec encodage UTF-8 explicite
        with open(env_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(env_content)
        
        print(f"✅ Nouveau fichier .env créé avec succès!")
        print(f"📍 Emplacement: {os.path.abspath(env_path)}")
        
        # Vérifier que le fichier peut être lu correctement
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = len(content.splitlines())
            print(f"✅ Vérification: {lines} lignes lues correctement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env: {e}")
        return False

def test_decouple():
    """Teste si python-decouple peut maintenant lire le fichier .env"""
    print("\n🧪 Test de python-decouple...")
    
    try:
        from decouple import config
        
        # Test de lecture des variables
        secret_key = config('SECRET_KEY', default='fallback')
        debug = config('DEBUG', default=True, cast=bool)
        
        print(f"✅ SECRET_KEY lu avec succès: {secret_key[:20]}...")
        print(f"✅ DEBUG lu avec succès: {debug}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    print("🚀 Réparation du fichier .env - Vidé-Grenier Kamer")
    print("=" * 55)
    
    # Vérifier le répertoire courant
    current_dir = os.getcwd()
    print(f"📂 Répertoire courant: {current_dir}")
    
    # Vérifier si nous sommes dans le bon dossier
    if not os.path.exists("manage.py"):
        print("⚠️  manage.py non trouvé. Assurez-vous d'être dans le dossier 'vide/'")
        return False
    
    # Réparer le fichier .env
    if fix_env_file():
        print("\n" + "=" * 55)
        
        # Tester python-decouple
        if test_decouple():
            print("\n🎉 Réparation terminée avec succès!")
            print("\n📋 Vous pouvez maintenant essayer:")
            print("   python manage.py check")
            print("   python manage.py collectstatic --noinput")
            print("   python manage.py runserver")
            return True
        else:
            print("\n⚠️  Problème avec python-decouple, essayez de le réinstaller:")
            print("   pip uninstall python-decouple -y")
            print("   pip install python-decouple==3.8")
            return False
    else:
        print("\n❌ Échec de la réparation du fichier .env")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)