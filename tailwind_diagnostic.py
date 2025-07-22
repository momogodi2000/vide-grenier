#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes Tailwind CSS
dans le projet Vidé-Grenier Kamer
"""

import os
import sys
from pathlib import Path
import json

def check_file_exists(filepath, description):
    """Vérifie si un fichier existe"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_directory_exists(dirpath, description):
    """Vérifie si un dossier existe"""
    exists = os.path.exists(dirpath) and os.path.isdir(dirpath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dirpath}")
    if exists:
        files = os.listdir(dirpath)
        if files:
            print(f"    📁 Contient {len(files)} fichier(s)")
        else:
            print(f"    📂 Dossier vide")
    return exists

def check_file_content(filepath, search_text, description):
    """Vérifie le contenu d'un fichier"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: Fichier non trouvé - {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found = search_text in content
            status = "✅" if found else "❌"
            print(f"{status} {description}: {search_text}")
            return found
    except Exception as e:
        print(f"❌ {description}: Erreur de lecture - {e}")
        return False

def analyze_django_settings():
    """Analyse les paramètres Django"""
    print("\n🔍 ANALYSE DES PARAMÈTRES DJANGO")
    print("-" * 40)
    
    settings_files = [
        'vide/settings/base.py',
        'vide/settings/development.py',
        'vide/settings/production.py'
    ]
    
    for settings_file in settings_files:
        if check_file_exists(settings_file, f"Fichier de paramètres"):
            # Vérifier la configuration des fichiers statiques
            check_file_content(settings_file, "STATIC_URL = '/static/'", "Configuration STATIC_URL")
            check_file_content(settings_file, "STATICFILES_DIRS", "Configuration STATICFILES_DIRS")
            check_file_content(settings_file, "BASE_DIR / 'static'", "Répertoire static dans STATICFILES_DIRS")
            check_file_content(settings_file, "whitenoise", "Configuration WhiteNoise")

def analyze_static_structure():
    """Analyse la structure des fichiers statiques"""
    print("\n🔍 ANALYSE DE LA STRUCTURE STATIQUE")
    print("-" * 40)
    
    # Vérifier les dossiers principaux
    static_dirs = [
        'static',
        'static/css',
        'static/js',
        'static/images',
        'staticfiles',
        'backend/static',
        'backend/static/backend'
    ]
    
    for directory in static_dirs:
        check_directory_exists(directory, f"Dossier")
    
    # Vérifier les fichiers CSS critiques
    css_files = [
        'static/css/tailwind.min.css',
        'static/css/custom.css',
        'static/css/animations.css',
        'static/css/input.css'
    ]
    
    for css_file in css_files:
        if check_file_exists(css_file, f"Fichier CSS"):
            # Vérifier la taille du fichier
            try:
                size = os.path.getsize(css_file)
                if size > 1024:
                    print(f"    📏 Taille: {size/1024:.1f} KB")
                else:
                    print(f"    ⚠️  Fichier très petit: {size} bytes")
            except:
                pass

def analyze_templates():
    """Analyse les templates"""
    print("\n🔍 ANALYSE DES TEMPLATES")
    print("-" * 40)
    
    template_files = [
        'templates/base.html',
        'backend/templates',
        'templates/components'
    ]
    
    for template in template_files:
        if os.path.isdir(template):
            check_directory_exists(template, f"Dossier de templates")
        else:
            if check_file_exists(template, f"Template"):
                # Vérifier le contenu du template
                check_file_content(template, "{% load static %}", "Chargement des fichiers statiques")
                check_file_content(template, "tailwind.min.css", "Référence Tailwind CSS")
                check_file_content(template, "custom.css", "Référence CSS personnalisé")

def analyze_tailwind_config():
    """Analyse la configuration Tailwind"""
    print("\n🔍 ANALYSE DE LA CONFIGURATION TAILWIND")
    print("-" * 40)
    
    # Vérifier les fichiers de configuration
    config_files = [
        'tailwind.config.js',
        'postcss.config.js',
        'package.json'
    ]
    
    for config_file in config_files:
        check_file_exists(config_file, f"Fichier de configuration")
    
    # Vérifier package.json plus en détail
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                
            if 'devDependencies' in package_data:
                deps = package_data['devDependencies']
                tailwind_installed = 'tailwindcss' in deps
                status = "✅" if tailwind_installed else "❌"
                print(f"{status} Tailwind CSS dans devDependencies")
                
                if tailwind_installed:
                    print(f"    📦 Version: {deps['tailwindcss']}")
            
            if 'scripts' in package_data:
                scripts = package_data['scripts']
                build_script = 'build-css' in scripts or 'build' in scripts
                status = "✅" if build_script else "❌"
                print(f"{status} Scripts de build configurés")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de package.json: {e}")

def analyze_gitignore():
    """Analyse le .gitignore"""
    print("\n🔍 ANALYSE DU .GITIGNORE")
    print("-" * 40)
    
    if check_file_exists('.gitignore', "Fichier .gitignore"):
        issues = []
        
        # Vérifier les exclusions problématiques
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '/static/' in content:
            issues.append("⚠️  /static/ exclu du versioning (peut causer des problèmes)")
        
        if '/staticfiles/' in content:
            print("✅ /staticfiles/ correctement exclu")
        
        if 'node_modules/' in content:
            print("✅ node_modules/ correctement exclu")
        
        for issue in issues:
            print(issue)

def check_permissions():
    """Vérifie les permissions des fichiers"""
    print("\n🔍 VÉRIFICATION DES PERMISSIONS")
    print("-" * 40)
    
    critical_files = [
        'manage.py',
        'static/css',
        'staticfiles'
    ]
    
    for filepath in critical_files:
        if os.path.exists(filepath):
            try:
                # Tester la lecture
                if os.path.isdir(filepath):
                    os.listdir(filepath)
                    print(f"✅ Permissions lecture OK: {filepath}")
                else:
                    with open(filepath, 'r') as f:
                        f.read(1)
                    print(f"✅ Permissions lecture OK: {filepath}")
            except PermissionError:
                print(f"❌ Permissions insuffisantes: {filepath}")
            except Exception as e:
                print(f"⚠️  Erreur de permission: {filepath} - {e}")

def provide_recommendations():
    """Fournit des recommandations basées sur l'analyse"""
    print("\n💡 RECOMMANDATIONS")
    print("-" * 40)
    
    recommendations = []
    
    # Vérifier les problèmes courants
    if not os.path.exists('static/css/tailwind.min.css'):
        recommendations.append("🔧 Générer le fichier Tailwind CSS manquant")
    
    if not os.path.exists('tailwind.config.js'):
        recommendations.append("🔧 Créer la configuration Tailwind")
    
    if not os.path.exists('package.json'):
        recommendations.append("🔧 Initialiser npm et installer Tailwind")
    
    if os.path.exists('static/css/tailwind.min.css'):
        try:
            size = os.path.getsize('static/css/tailwind.min.css')
            if size < 1024:  # Moins de 1KB
                recommendations.append("🔧 Le fichier Tailwind semble vide ou corrompu")
        except:
            pass
    
    if not recommendations:
        print("✅ Aucun problème majeur détecté!")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    print("\n🛠️  SOLUTIONS AUTOMATISÉES:")
    print("1. Exécuter le script de réparation complet")
    print("2. Utiliser le script de fallback si npm n'est pas disponible")
    print("3. Vérifier les paramètres Django dans settings/base.py")

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC TAILWIND CSS - VIDÉ-GRENIER KAMER")
    print("=" * 55)
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists('manage.py'):
        print("❌ manage.py non trouvé!")
        print("Assurez-vous d'être dans le dossier racine du projet Django")
        return False
    
    print("✅ Projet Django détecté")
    print(f"📂 Répertoire courant: {os.getcwd()}")
    
    # Exécuter les analyses
    analyze_django_settings()
    analyze_static_structure()
    analyze_templates()
    analyze_tailwind_config()
    analyze_gitignore()
    check_permissions()
    provide_recommendations()
    
    print("\n" + "=" * 55)
    print("🔍 DIAGNOSTIC TERMINÉ")
    print("=" * 55)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)