#!/usr/bin/env python3
"""
Script complet pour réparer Tailwind CSS dans Vidé-Grenier Kamer
Génère tous les fichiers nécessaires et configure le projet correctement
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def create_directory_structure():
    """Crée la structure des dossiers nécessaires"""
    print("🏗️  Création de la structure des dossiers...")
    
    directories = [
        'static',
        'static/css',
        'static/js',
        'static/images',
        'static/images/icons',
        'staticfiles',
        'node_modules',
        'backend/static',
        'backend/static/backend',
        'backend/static/backend/css',
        'backend/static/backend/js',
        'backend/static/backend/images'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Créé: {directory}")

def create_package_json():
    """Crée le package.json pour Tailwind CSS"""
    print("\n📦 Création du package.json...")
    
    package_json = {
        "name": "vide-grenier-kamer",
        "version": "2.5.0",
        "description": "Marketplace camerounaise de seconde main",
        "scripts": {
            "build-css": "tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --watch",
            "build-css-prod": "tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --minify",
            "dev": "tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --watch",
            "build": "tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.min.css --minify"
        },
        "devDependencies": {
            "tailwindcss": "^3.4.0",
            "@tailwindcss/forms": "^0.5.7",
            "@tailwindcss/typography": "^0.5.10",
            "@tailwindcss/aspect-ratio": "^0.4.2",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32"
        }
    }
    
    with open('package.json', 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2, ensure_ascii=False)
    
    print("✅ package.json créé")

def create_tailwind_config():
    """Crée la configuration Tailwind CSS"""
    print("\n⚙️  Création de la configuration Tailwind...")
    
    tailwind_config = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './backend/templates/**/*.html',
    './backend/static/**/*.js',
    './static/**/*.js',
    './backend/**/*.py',
  ],
  darkMode: 'class', // ou 'media' pour suivre les préférences système
  theme: {
    extend: {
      colors: {
        // Couleurs spécifiques à Vidé-Grenier Kamer
        'vgk-green': {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',  // Couleur principale
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        'vgk-orange': {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',  // Couleur secondaire
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        'vgk-gray': {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      },
      fontFamily: {
        'inter': ['Inter', 'system-ui', 'sans-serif'],
        'poppins': ['Poppins', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      boxShadow: {
        'vgk': '0 4px 6px -1px rgba(34, 197, 94, 0.1), 0 2px 4px -1px rgba(34, 197, 94, 0.06)',
        'vgk-lg': '0 10px 15px -3px rgba(34, 197, 94, 0.1), 0 4px 6px -2px rgba(34, 197, 94, 0.05)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}'''
    
    with open('tailwind.config.js', 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    
    print("✅ tailwind.config.js créé")

def create_postcss_config():
    """Crée la configuration PostCSS"""
    print("\n📝 Création de la configuration PostCSS...")
    
    postcss_config = '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
    
    with open('postcss.config.js', 'w', encoding='utf-8') as f:
        f.write(postcss_config)
    
    print("✅ postcss.config.js créé")

def create_input_css():
    """Crée le fichier CSS d'entrée pour Tailwind"""
    print("\n🎨 Création du fichier CSS d'entrée...")
    
    input_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

/* Styles personnalisés pour Vidé-Grenier Kamer */

@layer base {
  html {
    scroll-behavior: smooth;
  }
  
  body {
    @apply antialiased text-gray-900;
  }
  
  /* Styles pour les liens */
  a {
    @apply transition-colors duration-200;
  }
  
  /* Styles pour les boutons */
  button {
    @apply transition-all duration-200;
  }
  
  /* Styles pour les inputs */
  input, textarea, select {
    @apply transition-all duration-200;
  }
}

@layer components {
  /* Boutons principaux */
  .btn-primary {
    @apply bg-vgk-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-vgk-green-700 focus:ring-4 focus:ring-vgk-green-200 transition-all duration-200;
  }
  
  .btn-secondary {
    @apply bg-vgk-orange-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-vgk-orange-600 focus:ring-4 focus:ring-vgk-orange-200 transition-all duration-200;
  }
  
  .btn-outline {
    @apply border-2 border-vgk-green-600 text-vgk-green-600 px-6 py-3 rounded-lg font-medium hover:bg-vgk-green-600 hover:text-white focus:ring-4 focus:ring-vgk-green-200 transition-all duration-200;
  }
  
  /* Cards */
  .card {
    @apply bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300;
  }
  
  .card-product {
    @apply card overflow-hidden hover:transform hover:scale-105 transition-all duration-300;
  }
  
  /* Navigation */
  .nav-link {
    @apply text-gray-600 hover:text-vgk-green-600 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200;
  }
  
  .nav-link-active {
    @apply text-vgk-green-600 bg-vgk-green-50 px-3 py-2 rounded-md text-sm font-medium;
  }
  
  /* Forms */
  .form-input {
    @apply w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-4 focus:ring-vgk-green-200 focus:border-vgk-green-500 transition-all duration-200;
  }
  
  .form-label {
    @apply block text-sm font-medium text-gray-700 mb-2;
  }
  
  /* Messages/Alerts */
  .alert-success {
    @apply bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg;
  }
  
  .alert-error {
    @apply bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg;
  }
  
  .alert-warning {
    @apply bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg;
  }
  
  .alert-info {
    @apply bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg;
  }
}

@layer utilities {
  /* Utilitaires personnalisés */
  .text-gradient {
    @apply bg-gradient-to-r from-vgk-green-600 to-vgk-orange-500 bg-clip-text text-transparent;
  }
  
  .bg-gradient-vgk {
    @apply bg-gradient-to-br from-vgk-green-600 to-vgk-orange-500;
  }
  
  .shadow-vgk {
    box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.1), 0 2px 4px -1px rgba(34, 197, 94, 0.06);
  }
  
  /* Animations */
  .animate-fade-in {
    animation: fadeIn 0.5s ease-in-out;
  }
  
  .animate-slide-up {
    animation: slideUp 0.5s ease-out;
  }
  
  /* Responsive utilities */
  .container-vgk {
    @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8;
  }
}

/* Styles pour l'accessibilité */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.focus\\:not-sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 0;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}

/* Loading states */
.loading-skeleton {
  @apply animate-pulse bg-gray-200 rounded;
}

/* PWA styles */
.pwa-banner {
  @apply fixed top-0 left-0 right-0 bg-gradient-to-r from-vgk-green-600 to-vgk-orange-500 text-white p-4 z-50 transform -translate-y-full transition-transform duration-300;
}

.pwa-banner.show {
  @apply translate-y-0;
}

/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
  .dark\\:bg-gray-900 {
    background-color: #111827;
  }
  
  .dark\\:text-white {
    color: #ffffff;
  }
}'''
    
    os.makedirs('static/css', exist_ok=True)
    with open('static/css/input.css', 'w', encoding='utf-8') as f:
        f.write(input_css)
    
    print("✅ static/css/input.css créé")

def create_custom_css():
    """Crée le fichier CSS personnalisé"""
    print("\n🖌️  Création du CSS personnalisé...")
    
    custom_css = '''/* Custom CSS pour Vidé-Grenier Kamer - Styles additionnels */

/* Variables CSS pour cohérence */
:root {
  --vgk-green: #16a34a;
  --vgk-orange: #f97316;
  --vgk-gray: #6b7280;
  --border-radius: 0.75rem;
  --transition: all 0.2s ease-in-out;
}

/* Styles pour les icônes Lucide */
[data-lucide] {
  width: 1.25rem;
  height: 1.25rem;
  stroke-width: 2;
}

/* Styles pour les overlays de modal */
.modal-overlay {
  backdrop-filter: blur(8px);
  background-color: rgba(0, 0, 0, 0.6);
}

/* Styles pour les tooltips */
.tooltip {
  position: relative;
}

.tooltip::before {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: #1f2937;
  color: white;
  padding: 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: var(--transition);
  z-index: 1000;
}

.tooltip:hover::before {
  opacity: 1;
  visibility: visible;
}

/* Styles pour les dropdowns */
.dropdown-menu {
  transform: translateY(-10px);
  opacity: 0;
  visibility: hidden;
  transition: var(--transition);
}

.dropdown-menu.show {
  transform: translateY(0);
  opacity: 1;
  visibility: visible;
}

/* Styles pour les cartes de produits */
.product-card {
  transition: var(--transition);
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.product-image {
  aspect-ratio: 1;
  object-fit: cover;
  transition: var(--transition);
}

.product-card:hover .product-image {
  transform: scale(1.05);
}

/* Styles pour les badges */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-success {
  background-color: #dcfce7;
  color: #166534;
}

.badge-warning {
  background-color: #fef3c7;
  color: #92400e;
}

.badge-error {
  background-color: #fecaca;
  color: #991b1b;
}

/* Styles pour les notifications */
.notification {
  transform: translateX(100%);
  transition: var(--transition);
}

.notification.show {
  transform: translateX(0);
}

/* Styles pour les champs de recherche */
.search-input {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'%3e%3c/path%3e%3c/svg%3e");
  background-position: left 1rem center;
  background-repeat: no-repeat;
  background-size: 1.25rem;
  padding-left: 3rem;
}

/* Styles pour les tableaux responsifs */
.table-responsive {
  overflow-x: auto;
}

.table-responsive table {
  min-width: 600px;
}

/* Styles pour les formulaires */
.form-group {
  margin-bottom: 1.5rem;
}

.form-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.form-help {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Styles pour les pages de chargement */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid #e5e7eb;
  border-top: 2px solid var(--vgk-green);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Styles pour les images lazy loading */
.lazy-image {
  opacity: 0;
  transition: opacity 0.3s;
}

.lazy-image.loaded {
  opacity: 1;
}

/* Styles pour les messages de succès/erreur Django */
.messages {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  max-width: 400px;
}

.message {
  margin-bottom: 0.5rem;
  padding: 1rem;
  border-radius: var(--border-radius);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Styles responsive pour mobile */
@media (max-width: 640px) {
  .messages {
    top: 0;
    right: 0;
    left: 0;
    max-width: none;
    padding: 1rem;
  }
  
  .message {
    border-radius: 0;
  }
  
  .table-responsive {
    margin: 0 -1rem;
  }
  
  .container-vgk {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}

/* Améliorations pour l'accessibilité */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Focus visible pour la navigation au clavier */
.focus-visible:focus-visible {
  outline: 2px solid var(--vgk-green);
  outline-offset: 2px;
}

/* Styles pour les graphiques et statistiques */
.stat-card {
  background: linear-gradient(135deg, var(--vgk-green) 0%, var(--vgk-orange) 100%);
  color: white;
}

.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
  
  .print-break {
    page-break-before: always;
  }
}'''
    
    with open('static/css/custom.css', 'w', encoding='utf-8') as f:
        f.write(custom_css)
    
    print("✅ static/css/custom.css créé")

def create_animations_css():
    """Crée le fichier CSS pour les animations"""
    print("\n🎭 Création du CSS d'animations...")
    
    animations_css = '''/* Animations CSS pour Vidé-Grenier Kamer */

/* Keyframes pour les animations personnalisées */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    animation-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1);
    transform: translate3d(0, 0, 0);
  }
  40%, 43% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -30px, 0);
  }
  70% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -15px, 0);
  }
  90% {
    transform: translate3d(0, -4px, 0);
  }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
  20%, 40%, 60%, 80% { transform: translateX(10px); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
  100% { transform: translateY(0px); }
}

/* Classes d'animation */
.animate-fade-in { animation: fadeIn 0.6s ease-out; }
.animate-fade-in-up { animation: fadeInUp 0.6s ease-out; }
.animate-fade-in-down { animation: fadeInDown 0.6s ease-out; }
.animate-slide-in-left { animation: slideInLeft 0.6s ease-out; }
.animate-slide-in-right { animation: slideInRight 0.6s ease-out; }
.animate-scale-in { animation: scaleIn 0.4s ease-out; }
.animate-bounce { animation: bounce 1s infinite; }
.animate-pulse-slow { animation: pulse 2s infinite; }
.animate-shake { animation: shake 0.6s ease-in-out; }
.animate-rotate { animation: rotate 1s linear infinite; }
.animate-float { animation: float 3s ease-in-out infinite; }

/* Delays pour les animations en cascade */
.animate-delay-100 { animation-delay: 0.1s; }
.animate-delay-200 { animation-delay: 0.2s; }
.animate-delay-300 { animation-delay: 0.3s; }
.animate-delay-500 { animation-delay: 0.5s; }
.animate-delay-700 { animation-delay: 0.7s; }
.animate-delay-1000 { animation-delay: 1s; }

/* Transitions personnalisées */
.transition-all { transition: all 0.3s ease-in-out; }
.transition-fast { transition: all 0.15s ease-in-out; }
.transition-slow { transition: all 0.5s ease-in-out; }

/* Hover effects */
.hover-lift {
  transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
}

.hover-lift:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.hover-grow {
  transition: transform 0.3s ease-in-out;
}

.hover-grow:hover {
  transform: scale(1.05);
}

.hover-brightness {
  transition: filter 0.3s ease-in-out;
}

.hover-brightness:hover {
  filter: brightness(1.1);
}

/* Loading animations */
.loading-dots {
  display: inline-block;
}

.loading-dots:after {
  content: '...';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { color: rgba(0,0,0,0); text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  40% { color: black; text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  60% { text-shadow: .25em 0 0 black, .5em 0 0 rgba(0,0,0,0); }
  80%, 100% { text-shadow: .25em 0 0 black, .5em 0 0 black; }
}

/* Smooth scroll */
html {
  scroll-behavior: smooth;
}

/* Parallax effect */
.parallax {
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}

/* Glassmorphism effect */
.glass {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

/* Stagger animations for lists */
.stagger-children > * {
  animation: fadeInUp 0.6s ease-out;
}

.stagger-children > *:nth-child(1) { animation-delay: 0.1s; }
.stagger-children > *:nth-child(2) { animation-delay: 0.2s; }
.stagger-children > *:nth-child(3) { animation-delay: 0.3s; }
.stagger-children > *:nth-child(4) { animation-delay: 0.4s; }
.stagger-children > *:nth-child(5) { animation-delay: 0.5s; }
.stagger-children > *:nth-child(6) { animation-delay: 0.6s; }'''
    
    with open('static/css/animations.css', 'w', encoding='utf-8') as f:
        f.write(animations_css)
    
    print("✅ static/css/animations.css créé")

def update_base_template():
    """Met à jour le template de base pour une meilleure intégration Tailwind"""
    print("\n📄 Mise à jour du template de base...")
    
    base_template = '''{% load static %}
<!DOCTYPE html>
<html lang="fr" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    
    <!-- SEO Meta Tags -->
    <title>{% block title %}Vidé-Grenier Kamer - Marketplace camerounaise{% endblock %}</title>
    <meta name="description" content="{% block description %}Marketplace camerounaise de seconde main. Vendez et achetez facilement avec des moyens de paiement locaux.{% endblock %}">
    <meta name="keywords" content="vidé-grenier, marketplace, Cameroun, seconde main, vente, achat">
    <meta name="author" content="Vidé-Grenier Kamer">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{% block og_title %}Vidé-Grenier Kamer{% endblock %}">
    <meta property="og:description" content="{% block og_description %}Marketplace camerounaise de seconde main{% endblock %}">
    <meta property="og:image" content="{% static 'images/og-image.jpg' %}">
    <meta property="og:url" content="{{ request.build_absolute_uri }}">
    <meta property="og:type" content="website">
    
    <!-- Favicons -->
    <link rel="icon" type="image/x-icon" href="{% static 'images/favicon.ico' %}">
    <link rel="icon" type="image/png" sizes="32x32" href="{% static 'images/favicon-32x32.png' %}">
    <link rel="icon" type="image/png" sizes="16x16" href="{% static 'images/favicon-16x16.png' %}">
    <link rel="apple-touch-icon" href="{% static 'images/icons/icon-192x192.png' %}">
    <link rel="manifest" href="{% url 'manifest' %}">
    
    <!-- Theme Color -->
    <meta name="theme-color" content="#16a34a">
    <meta name="msapplication-TileColor" content="#16a34a">
    
    <!-- Preconnect to External Resources -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    
    <!-- Critical CSS - Inline for performance -->
    <style>
        /* Critical styles inlined for faster loading */
        html { scroll-behavior: smooth; }
        body { font-family: 'Inter', system-ui, sans-serif; }
        .loading-fallback { display: flex; justify-content: center; align-items: center; min-height: 50vh; }
        .loading-spinner { width: 2rem; height: 2rem; border: 2px solid #e5e7eb; border-top: 2px solid #16a34a; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
    
    <!-- Main CSS Files -->
    <link href="{% static 'css/tailwind.min.css' %}" rel="stylesheet">
    <link href="{% static 'css/custom.css' %}" rel="stylesheet">
    <link href="{% static 'css/animations.css' %}" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Custom CSS Block -->
    {% block extra_css %}{% endblock %}
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Vidé-Grenier Kamer",
        "url": "{{ request.build_absolute_uri }}",
        "logo": "{% static 'images/logo.png' %}",
        "description": "Marketplace camerounaise de seconde main",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "CM",
            "addressLocality": "Douala"
        }
    }
    </script>
</head>

<body class="bg-gray-50 font-inter antialiased min-h-full">
    <!-- Skip to main content for accessibility -->
    <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-vgk-green-600 text-white px-4 py-2 rounded-md z-50 transition-all">
        Aller au contenu principal
    </a>
    
    <!-- Loading Screen -->
    <div id="loading-screen" class="fixed inset-0 bg-gradient-to-br from-vgk-green-600 to-vgk-orange-500 z-50 flex items-center justify-center">
        <div class="text-center text-white animate-fade-in">
            <div class="loading-spinner mx-auto mb-4"></div>
            <h2 class="text-2xl font-bold mb-2">Vidé-Grenier Kamer</h2>
            <p class="text-lg opacity-90">Chargement en cours...</p>
        </div>
    </div>
    
    <!-- PWA Install Banner -->
    <div id="pwa-banner" class="hidden fixed top-0 left-0 right-0 bg-gradient-to-r from-vgk-green-600 to-vgk-orange-500 text-white p-4 z-40">
        <div class="container mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <i data-lucide="smartphone" class="w-6 h-6"></i>
                <div>
                    <p class="font-medium">Installer l'application</p>
                    <p class="text-sm opacity-90">Accédez rapidement à VGK depuis votre écran d'accueil</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <button id="pwa-install-btn" class="bg-white text-vgk-green-600 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors">
                    Installer
                </button>
                <button id="pwa-close-btn" class="text-white/80 hover:text-white transition-colors">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Navigation -->
    {% include 'components/navbar.html' %}
    
    <!-- Flash Messages -->
    {% if messages %}
    <div class="messages fixed top-20 right-4 z-30 space-y-2" id="messages-container">
        {% for message in messages %}
        <div class="message animate-slide-in-right alert-{{ message.tags }} max-w-sm">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    {% if message.tags == 'success' %}
                        <i data-lucide="check-circle" class="w-5 h-5 text-green-600"></i>
                    {% elif message.tags == 'error' %}
                        <i data-lucide="alert-circle" class="w-5 h-5 text-red-600"></i>
                    {% elif message.tags == 'warning' %}
                        <i data-lucide="alert-triangle" class="w-5 h-5 text-yellow-600"></i>
                    {% else %}
                        <i data-lucide="info" class="w-5 h-5 text-blue-600"></i>
                    {% endif %}
                    <span class="text-sm">{{ message }}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600 ml-2">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Main Content -->
    <main id="main-content" class="min-h-screen">
        {% block content %}
        <div class="loading-fallback">
            <div class="loading-spinner"></div>
        </div>
        {% endblock %}
    </main>
    
    <!-- Footer -->
    {% include 'components/footer.html' %}
    
    <!-- Back to Top Button -->
    <button id="back-to-top" class="fixed bottom-6 right-6 bg-vgk-green-600 text-white p-3 rounded-full shadow-lg hover:bg-vgk-green-700 transition-all transform translate-y-16 opacity-0 z-30">
        <i data-lucide="arrow-up" class="w-5 h-5"></i>
    </button>
    
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    
    <!-- Main JavaScript -->
    <script src="{% static 'js/app.js' %}" defer></script>
    
    {% block extra_js %}{% endblock %}
    
    <!-- Initialize Lucide Icons -->
    <script>
        // Initialize Lucide icons when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            
            // Hide loading screen
            const loadingScreen = document.getElementById('loading-screen');
            if (loadingScreen) {
                setTimeout(() => {
                    loadingScreen.style.opacity = '0';
                    setTimeout(() => loadingScreen.remove(), 300);
                }, 500);
            }
            
            // Auto-hide messages after 5 seconds
            const messages = document.querySelectorAll('.message');
            messages.forEach(message => {
                setTimeout(() => {
                    message.style.opacity = '0';
                    message.style.transform = 'translateX(100%)';
                    setTimeout(() => message.remove(), 300);
                }, 5000);
            });
            
            // Back to top functionality
            const backToTopBtn = document.getElementById('back-to-top');
            window.addEventListener('scroll', () => {
                if (window.pageYOffset > 300) {
                    backToTopBtn.classList.remove('translate-y-16', 'opacity-0');
                } else {
                    backToTopBtn.classList.add('translate-y-16', 'opacity-0');
                }
            });
            
            backToTopBtn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    </script>
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {
                        console.log('SW registered: ', registration);
                    })
                    .catch(function(registrationError) {
                        console.log('SW registration failed: ', registrationError);
                    });
            });
        }
    </script>
</body>
</html>'''
    
    os.makedirs('templates', exist_ok=True)
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    print("✅ templates/base.html mis à jour")

def install_tailwind():
    """Installe Tailwind CSS et génère le fichier CSS"""
    print("\n📦 Installation de Tailwind CSS...")
    
    try:
        # Installer les dépendances npm
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dépendances npm installées")
        else:
            print("⚠️  npm install a échoué, essayons de continuer...")
            print(result.stderr)
        
        # Générer le CSS Tailwind
        print("🎨 Génération du CSS Tailwind...")
        result = subprocess.run(['npx', 'tailwindcss', '-i', './static/css/input.css', '-o', './static/css/tailwind.min.css', '--minify'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CSS Tailwind généré avec succès")
        else:
            print("⚠️  Génération Tailwind échouée, création d'un fallback...")
            create_fallback_tailwind()
            
    except FileNotFoundError:
        print("⚠️  npm non trouvé, création d'un fallback Tailwind...")
        create_fallback_tailwind()

def create_fallback_tailwind():
    """Crée un fallback Tailwind CSS si npm n'est pas disponible"""
    print("🔄 Création d'un fallback Tailwind CSS...")
    
    # CSS de base avec les principales classes Tailwind utilisées
    fallback_css = '''/* Fallback Tailwind CSS pour Vidé-Grenier Kamer */

/* Reset et base */
*, ::before, ::after { box-sizing: border-box; border-width: 0; border-style: solid; border-color: #e5e7eb; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; tab-size: 4; font-family: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"; }
body { margin: 0; line-height: inherit; }

/* Couleurs personnalisées VGK */
:root {
  --vgk-green-50: #f0fdf4;
  --vgk-green-100: #dcfce7;
  --vgk-green-600: #16a34a;
  --vgk-green-700: #15803d;
  --vgk-orange-500: #f97316;
  --vgk-orange-600: #ea580c;
}

/* Layout */
.container { width: 100%; margin-left: auto; margin-right: auto; padding-left: 1rem; padding-right: 1rem; }
@media (min-width: 640px) { .container { max-width: 640px; } }
@media (min-width: 768px) { .container { max-width: 768px; } }
@media (min-width: 1024px) { .container { max-width: 1024px; } }
.mx-auto { margin-left: auto; margin-right: auto; }
.min-h-screen { min-height: 100vh; }
.min-h-full { min-height: 100%; }
.h-full { height: 100%; }

/* Flexbox */
.flex { display: flex; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.space-x-2 > :not([hidden]) ~ :not([hidden]) { margin-left: 0.5rem; }
.space-x-3 > :not([hidden]) ~ :not([hidden]) { margin-left: 0.75rem; }
.space-x-4 > :not([hidden]) ~ :not([hidden]) { margin-left: 1rem; }
.space-y-2 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.5rem; }
.space-y-4 > :not([hidden]) ~ :not([hidden]) { margin-top: 1rem; }

/* Grid */
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }

/* Positioning */
.relative { position: relative; }
.absolute { position: absolute; }
.fixed { position: fixed; }
.inset-0 { top: 0; right: 0; bottom: 0; left: 0; }
.top-0 { top: 0; }
.right-0 { right: 0; }
.bottom-0 { bottom: 0; }
.left-0 { left: 0; }
.z-30 { z-index: 30; }
.z-40 { z-index: 40; }
.z-50 { z-index: 50; }

/* Spacing */
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.m-4 { margin: 1rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-4 { margin-top: 1rem; }

/* Colors */
.bg-white { background-color: #ffffff; }
.bg-gray-50 { background-color: #f9fafb; }
.bg-gray-100 { background-color: #f3f4f6; }
.bg-green-600 { background-color: var(--vgk-green-600); }
.bg-green-700 { background-color: var(--vgk-green-700); }
.bg-orange-500 { background-color: var(--vgk-orange-500); }
.text-white { color: #ffffff; }
.text-gray-600 { color: #4b5563; }
.text-gray-800 { color: #1f2937; }
.text-gray-900 { color: #111827; }
.text-green-600 { color: var(--vgk-green-600); }

/* Typography */
.font-inter { font-family: 'Inter', system-ui, sans-serif; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.text-sm { font-size: 0.875rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }
.text-2xl { font-size: 1.5rem; }
.text-center { text-align: center; }
.antialiased { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

/* Borders */
.border { border-width: 1px; }
.border-gray-300 { border-color: #d1d5db; }
.rounded { border-radius: 0.25rem; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-full { border-radius: 9999px; }

/* Shadows */
.shadow { box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
.shadow-xl { box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }

/* Width & Height */
.w-4 { width: 1rem; }
.w-5 { width: 1.25rem; }
.w-6 { width: 1.5rem; }
.w-full { width: 100%; }
.h-4 { height: 1rem; }
.h-5 { height: 1.25rem; }
.h-6 { height: 1.5rem; }
.h-32 { height: 8rem; }

/* Display */
.block { display: block; }
.inline-block { display: inline-block; }
.hidden { display: none; }

/* Opacity */
.opacity-0 { opacity: 0; }
.opacity-90 { opacity: 0.9; }

/* Transform */
.transform { transform: translateX(var(--tw-translate-x, 0)) translateY(var(--tw-translate-y, 0)) rotate(var(--tw-rotate, 0)) skewX(var(--tw-skew-x, 0)) skewY(var(--tw-skew-y, 0)) scaleX(var(--tw-scale-x, 1)) scaleY(var(--tw-scale-y, 1)); }
.translate-y-16 { --tw-translate-y: 4rem; }

/* Transitions */
.transition-all { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }
.transition-colors { transition-property: color, background-color, border-color, text-decoration-color, fill, stroke; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }

/* Hover states */
.hover\\:bg-green-700:hover { background-color: var(--vgk-green-700); }
.hover\\:bg-gray-100:hover { background-color: #f3f4f6; }
.hover\\:text-white:hover { color: #ffffff; }

/* Focus states */
.focus\\:ring-4:focus { --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color); --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(4px + var(--tw-ring-offset-width)) var(--tw-ring-color); box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000); }
.focus\\:not-sr-only:focus { position: static; width: auto; height: auto; padding: 0; margin: 0; overflow: visible; clip: auto; white-space: normal; }

/* Screen reader only */
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border-width: 0; }

/* Animation classes */
.animate-spin { animation: spin 1s linear infinite; }
.animate-fade-in { animation: fadeIn 0.6s ease-out; }
.animate-slide-in-right { animation: slideInRight 0.6s ease-out; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideInRight { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }

/* Gradient backgrounds */
.bg-gradient-to-br { background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }
.bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops)); }
.from-green-600 { --tw-gradient-from: var(--vgk-green-600); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(22, 163, 74, 0)); }
.to-orange-500 { --tw-gradient-to: var(--vgk-orange-500); }

/* Custom VGK components */
.btn-primary { background-color: var(--vgk-green-600); color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 500; transition: all 0.2s; border: none; cursor: pointer; }
.btn-primary:hover { background-color: var(--vgk-green-700); }

.card { background-color: white; border-radius: 0.75rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); transition: all 0.3s; }
.card:hover { box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }

.alert-success { background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 1rem; border-radius: 0.5rem; }
.alert-error { background-color: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 1rem; border-radius: 0.5rem; }
.alert-warning { background-color: #fffbeb; border: 1px solid #fed7aa; color: #92400e; padding: 1rem; border-radius: 0.5rem; }
.alert-info { background-color: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; padding: 1rem; border-radius: 0.5rem; }

/* Responsive utilities */
@media (min-width: 640px) {
  .sm\\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
}

@media (min-width: 1024px) {
  .lg\\:px-8 { padding-left: 2rem; padding-right: 2rem; }
}
'''
    
    with open('static/css/tailwind.min.css', 'w', encoding='utf-8') as f:
        f.write(fallback_css)
    
    print("✅ Fallback Tailwind CSS créé")

def update_django_settings():
    """Met à jour les paramètres Django pour les fichiers statiques"""
    print("\n⚙️  Mise à jour des paramètres Django...")
    
    # Lire le fichier settings actuel
    try:
        with open('vide/settings/base.py', 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        # Vérifier si les paramètres sont déjà corrects
        if 'STATICFILES_FINDERS' in settings_content:
            print("✅ Paramètres Django déjà configurés")
            return
        
        # Ajouter la configuration des fichiers statiques
        static_config = '''
# Static files configuration optimisée
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuration WhiteNoise améliorée
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Headers pour les fichiers statiques
WHITENOISE_MAX_AGE = 31536000  # 1 an pour les fichiers avec hash
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# Compression des fichiers CSS/JS
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = config('DEBUG', default=False, cast=bool)
'''
        
        # Insérer la configuration après la configuration des fichiers statiques existante
        if "STATIC_URL = '/static/'" in settings_content:
            settings_content = settings_content.replace(
                "MEDIA_ROOT = BASE_DIR / 'media'",
                f"MEDIA_ROOT = BASE_DIR / 'media'\n{static_config}"
            )
        
        # Réécrire le fichier
        with open('vide/settings/base.py', 'w', encoding='utf-8') as f:
            f.write(settings_content)
        
        print("✅ Paramètres Django mis à jour")
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la mise à jour des paramètres: {e}")

def create_build_script():
    """Crée un script de build pour automatiser le processus"""
    print("\n🔨 Création du script de build...")
    
    build_script = '''#!/usr/bin/env python3
"""
Script de build automatisé pour Vidé-Grenier Kamer
"""

import subprocess
import sys
import os

def run_command(command, description):
    print(f"\\n🔄 {description}...")
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
        run_command('find staticfiles -name "*.css" -exec gzip -k {} \\;', 'Compression CSS')
        run_command('find staticfiles -name "*.js" -exec gzip -k {} \\;', 'Compression JS')
    
    print("\\n🎉 Build terminé!")

if __name__ == "__main__":
    main()
'''
    
    with open('build.py', 'w', encoding='utf-8') as f:
        f.write(build_script)
    
    # Rendre le script exécutable sur Unix
    try:
        os.chmod('build.py', 0o755)
    except:
        pass
    
    print("✅ build.py créé")

def create_dev_script():
    """Crée un script de développement"""
    print("\n🛠️  Création du script de développement...")
    
    dev_script = '''#!/usr/bin/env python3
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
        print("\\n🛑 Arrêt du serveur de développement")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
    
    with open('dev.py', 'w', encoding='utf-8') as f:
        f.write(dev_script)
    
    try:
        os.chmod('dev.py', 0o755)
    except:
        pass
    
    print("✅ dev.py créé")

def main():
    """Fonction principale"""
    print("🚀 Réparation complète de Tailwind CSS - Vidé-Grenier Kamer")
    print("=" * 65)
    
    try:
        # Vérifier qu'on est dans le bon dossier
        if not os.path.exists('manage.py'):
            print("❌ manage.py non trouvé. Assurez-vous d'être dans le dossier 'vide/'")
            return False
        
        # Étapes de réparation
        create_directory_structure()
        create_package_json()
        create_tailwind_config()
        create_postcss_config()
        create_input_css()
        create_custom_css()
        create_animations_css()
        update_base_template()
        install_tailwind()
        update_django_settings()
        create_build_script()
        create_dev_script()
        
        print("\\n" + "=" * 65)
        print("🎉 RÉPARATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 65)
        
        print("\\n📋 Prochaines étapes:")
        print("1. Installer Node.js si pas encore fait: https://nodejs.org/")
        print("2. Exécuter: npm install")
        print("3. Build CSS: npm run build-css-prod")
        print("4. Collecter les statiques: python manage.py collectstatic")
        print("5. Démarrer le serveur: python manage.py runserver")
        
        print("\\n🛠️  Scripts disponibles:")
        print("- python build.py    # Build complet pour production")
        print("- python dev.py      # Mode développement avec watch")
        
        print("\\n🎨 Fichiers CSS générés:")
        print("- static/css/tailwind.min.css  # CSS Tailwind compilé")
        print("- static/css/custom.css        # Styles personnalisés VGK")
        print("- static/css/animations.css    # Animations CSS")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Erreur lors de la réparation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

def create_animations_css():
    """Crée le fichier CSS pour les animations"""
    print("\n🎭 Création du CSS d'animations...")
    
    animations_css = '''/* Animations CSS pour Vidé-Grenier Kamer */

/* Keyframes pour les animations personnalisées */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    animation-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1);
    transform: translate3d(0, 0, 0);
  }
  40%, 43% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -30px, 0);
  }
  70% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -15px, 0);
  }
  90% {
    transform: translate3d(0, -4px, 0);
  }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
  20%, 40%, 60%, 80% { transform: translateX(10px); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
  100% { transform: translateY(0px); }
}

/* Classes d'animation */
.animate-fade-in { animation: fadeIn 0.6s ease-out; }
.animate-fade-in-up { animation: fadeInUp 0.6s ease-out; }
.animate-fade-in-down { animation: fadeInDown 0.6s ease-out; }
.animate-slide-in-left { animation: slideInLeft 0.6s ease-out; }
.animate-slide-in-right { animation: slideInRight 0.6s ease-out; }
.animate-scale-in { animation: scaleIn 0.4s ease-out; }
.animate-bounce { animation: bounce 1s infinite; }
.animate-pulse-slow { animation: pulse 2s infinite; }
.animate-shake { animation: shake 0.6s ease-in-out; }
.animate-rotate { animation: rotate 1s linear infinite; }
.animate-float { animation: float 3s ease-in-out infinite; }

/* Delays pour les animations en cascade */
.animate-delay-100 { animation-delay: 0.1s; }
.animate-delay-200 { animation-delay: 0.2s; }
.animate-delay-300 { animation-delay: 0.3s; }
.animate-delay-500 { animation-delay: 0.5s; }
.animate-delay-700 { animation-delay: 0.7s; }
.animate-delay-1000 { animation-delay: 1s; }

/* Transitions personnalisées */
.transition-all { transition: all 0.3s ease-in-out; }
.transition-fast { transition: all 0.15s ease-in-out; }
.transition-slow { transition: all 0.5s ease-in-out; }

/* Hover effects */
.hover-lift {
  transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
}

.hover-lift:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.hover-grow {
  transition: transform 0.3s ease-in-out;
}

.hover-grow:hover {
  transform: scale(1.05);
}

.hover-brightness {
  transition: filter 0.3s ease-in-out;
}

.hover-brightness:hover {
  filter: brightness(1.1);
}

/* Loading animations */
.loading-dots {
  display: inline-block;
}

.loading-dots:after {
  content: '...';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { color: rgba(0,0,0,0); text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  40% { color: black; text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  60% { text-shadow: .25em 0 0 black, .5em 0 0 rgba(0,0,0,0); }
  80%, 100% { text-shadow: .25em 0 0 black, .5em 0 0 black; }
}

/* Smooth scroll */
html {
  scroll-behavior: smooth;
}

/* Parallax effect */
.parallax {
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}

/* Glassmorphism effect */
.glass {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

/* Stagger animations for lists */
.stagger-children > * {
  animation: fadeInUp 0.6s ease-out;
}

.stagger-children > *:nth-child(1) { animation-delay: 0.1s; }
.stagger-children > *:nth-child(2) { animation-delay: 0.2s; }
.stagger-children > *:nth-child(3) { animation-delay: 0.3s; }
.stagger-children > *:nth-child(4) { animation-delay: 0.4s; }
.stagger-children > *:nth-child(5) { animation-delay: 0.5s; }
.stagger-children > *:nth-child(6) { animation-delay: 0.6s; }'''