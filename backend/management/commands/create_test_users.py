# backend/management/__init__.py
# Fichier vide pour faire de ce dossier un package Python

# backend/management/commands/__init__.py  
# Fichier vide pour faire de ce dossier un package Python

# backend/management/commands/create_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from backend.models import Category, Product, ProductImage, Order, Review
import random
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Créer des utilisateurs de test et des données de démonstration pour VGK'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--with-demo-data',
            action='store_true',
            help='Créer aussi des données de démonstration (produits, commandes, etc.)',
        )
        
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Supprimer les utilisateurs de test existants avant de créer les nouveaux',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Création des utilisateurs de test pour Vidé-Grenier Kamer')
        )
        
        # Supprimer les utilisateurs existants si demandé
        if options['clear_existing']:
            self.clear_existing_test_users()
        
        # Créer les utilisateurs de test
        with transaction.atomic():
            # 2 Super Admins
            self.create_admin_users()
            
            # 5 Utilisateurs clients de test
            test_users = self.create_test_clients()
            
            # Créer des données de démonstration si demandé
            if options['with_demo_data']:
                self.create_demo_categories()
                self.create_demo_products(test_users)
                # self.create_demo_orders(test_users)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Tous les utilisateurs de test ont été créés avec succès!')
        )
        # self.display_created_users()  # Removed: method does not exist. If you want to display users, implement or use another method.
    
    def clear_existing_test_users(self):
        """Supprimer les utilisateurs de test existants"""
        self.stdout.write('🧹 Suppression des utilisateurs de test existants...')
        
        test_emails = [
            'admin@vgk.com', 'superadmin@vgk.com',
            'alice.douala@gmail.com', 'bob.yaounde@gmail.com', 
            'claire.bafoussam@gmail.com', 'david.garoua@gmail.com',
            'emma.bamenda@gmail.com'
        ]
        
        deleted_count = User.objects.filter(email__in=test_emails).delete()[0]
        self.stdout.write(f'   Supprimé {deleted_count} utilisateurs existants')
    
    def create_admin_users(self):
        """Créer 2 super administrateurs avec tous les privilèges"""
        self.stdout.write('👑 Création des super administrateurs...')
        
        admin_data = [
            {
                'email': 'admin@vgk.com',
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'Principal',
                'phone': '+237694638412',
                'city': 'DOUALA',
                'address': '123 Avenue Ahidjo, Akwa, Douala',
                'user_type': 'ADMIN'
            },
            {
                'email': 'superadmin@vgk.com', 
                'username': 'superadmin',
                'first_name': 'Super',
                'last_name': 'Administrateur',
                'phone': '+237694638413',
                'city': 'YAOUNDE',
                'address': '456 Avenue Kennedy, Centre-ville, Yaoundé',
                'user_type': 'ADMIN'
            }
        ]
        
        for admin_info in admin_data:
            admin_user = User.objects.create_user(
                username=admin_info['username'],
                email=admin_info['email'],
                password='AdminVGK2025!',  # Mot de passe sécurisé
                first_name=admin_info['first_name'],
                last_name=admin_info['last_name'],
                phone=admin_info['phone'],
                city=admin_info['city'],
                address=admin_info['address'],
                user_type=admin_info['user_type'],
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                phone_verified=True,
                trust_score=100,
                loyalty_points=10000
            )
            
            self.stdout.write(
                f'   ✅ Admin créé: {admin_user.email} (mot de passe: c)'
            )
    
    def create_test_clients(self):
        """Créer 5 utilisateurs clients de test"""
        self.stdout.write('👥 Création des clients de test...')
        
        client_data = [
            {
                'email': 'alice.douala@gmail.com',
                'first_name': 'Alice',
                'last_name': 'Mballa',
                'phone': '+237677123456',
                'city': 'DOUALA',
                'address': 'Quartier Bonanjo, Rue des Flamboyants, Douala',
                'loyalty_points': 2500
            },
            {
                'email': 'bob.yaounde@gmail.com',
                'first_name': 'Bob',
                'last_name': 'Fomba',
                'phone': '+237682234567',
                'city': 'YAOUNDE',
                'address': 'Bastos, Avenue Charles de Gaulle, Yaoundé',
                'loyalty_points': 1800
            },
            {
                'email': 'claire.bafoussam@gmail.com',
                'first_name': 'Claire',
                'last_name': 'Tchatchou',
                'phone': '+237693345678',
                'city': 'BAFOUSSAM',
                'address': 'Centre-ville, Rue de la Poste, Bafoussam',
                'loyalty_points': 3200
            },
            {
                'email': 'david.garoua@gmail.com',
                'first_name': 'David',
                'last_name': 'Mahamat',
                'phone': '+237654456789',
                'city': 'GAROUA',
                'address': 'Plateau, Avenue Ahmadou Ahidjo, Garoua',
                'loyalty_points': 1200
            },
            {
                'email': 'emma.bamenda@gmail.com',
                'first_name': 'Emma',
                'last_name': 'Nkemtendong',
                'phone': '+237675567890',
                'city': 'BAMENDA',
                'address': 'Commercial Avenue, Up Station, Bamenda',
                'loyalty_points': 4100
            }
        ]
        
        created_users = []
        
        for client_info in client_data:
            client_user = User.objects.create_user(
                username=client_info['email'].split('@')[0],  # Utiliser la partie avant @ comme username
                email=client_info['email'],
                password='TestVGK2025!',  # Mot de passe commun pour les tests
                first_name=client_info['first_name'],
                last_name=client_info['last_name'],
                phone=client_info['phone'],
                city=client_info['city'],
                address=client_info['address'],
                user_type='CLIENT',
                is_verified=True,
                phone_verified=True,
                trust_score=random.randint(80, 100),
                loyalty_points=client_info['loyalty_points']
            )
            
            created_users.append(client_user)
            
            self.stdout.write(
                f'   ✅ Client créé: {client_user.get_full_name()} ({client_user.email})'
            )
        
        return created_users
    
    def create_demo_categories(self):
        """Créer des catégories de démonstration"""
        self.stdout.write('📂 Création des catégories de démonstration...')
        
        categories_data = [
            # Catégories principales avec leurs sous-catégories
            {
                'name': 'Femme',
                'slug': 'femme',
                'icon': '👩',
                'children': [
                    {'name': 'Vêtements', 'slug': 'femme-vetements'},
                    {'name': 'Chaussures', 'slug': 'femme-chaussures'},
                    {'name': 'Accessoires', 'slug': 'femme-accessoires'},
                    {'name': 'Beauté', 'slug': 'femme-beaute'}
                ]
            },
            {
                'name': 'Homme',
                'slug': 'homme',
                'icon': '👨',
                'children': [
                    {'name': 'Vêtements', 'slug': 'homme-vetements'},
                    {'name': 'Chaussures', 'slug': 'homme-chaussures'},
                    {'name': 'Accessoires', 'slug': 'homme-accessoires'}
                ]
            },
            {
                'name': 'Enfants',
                'slug': 'enfants',
                'icon': '👶',
                'children': [
                    {'name': 'Vêtements bébé', 'slug': 'enfants-bebe'},
                    {'name': 'Jouets', 'slug': 'enfants-jouets'},
                    {'name': 'Matériel puériculture', 'slug': 'enfants-puericulture'}
                ]
            },
            {
                'name': 'Électronique',
                'slug': 'electronique',
                'icon': '📱',
                'children': [
                    {'name': 'Smartphones', 'slug': 'electronique-smartphones'},
                    {'name': 'Ordinateurs', 'slug': 'electronique-ordinateurs'},
                    {'name': 'TV & Audio', 'slug': 'electronique-tv-audio'}
                ]
            },
            {
                'name': 'Maison',
                'slug': 'maison',
                'icon': '🏠',
                'children': [
                    {'name': 'Mobilier', 'slug': 'maison-mobilier'},
                    {'name': 'Électroménager', 'slug': 'maison-electromenager'},
                    {'name': 'Décoration', 'slug': 'maison-decoration'}
                ]
            }
        ]
        
        for cat_data in categories_data:
            # Créer la catégorie parent
            parent_cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                slug=cat_data['slug'],
                defaults={
                    'icon': cat_data['icon'],
                    'is_active': True,
                    'order': 0
                }
            )
            
            if created:
                self.stdout.write(f'   ✅ Catégorie parent: {parent_cat.name}')
            
            # Créer les sous-catégories
            for child_data in cat_data['children']:
                child_cat, created = Category.objects.get_or_create(
                    name=child_data['name'],
                    slug=child_data['slug'],
                    defaults={
                        'parent': parent_cat,
                        'is_active': True,
                        'order': 0
                    }
                )
                
                if created:
                    self.stdout.write(f'      ↳ Sous-catégorie: {child_cat.name}')
    
    def create_demo_products(self, users):
        """Créer des produits de démonstration"""
        self.stdout.write('🛍️ Création des produits de démonstration...')
        
        # Récupérer quelques catégories
        categories = Category.objects.filter(children=None, is_active=True)[:10]
        
        if not categories:
            self.stdout.write(
                self.style.WARNING('   ⚠️ Aucune catégorie trouvée, créez d\'abord les catégories')
            )
            return
        
        products_data = [
            {
                'title': 'iPhone 12 Pro 128GB Excellent État',
                'description': 'iPhone 12 Pro en excellent état, acheté il y a 6 mois. Aucune rayure, batterie à 95%. Vendu avec chargeur et boîte d\'origine. Débloqué tous opérateurs.',
                'price': Decimal('450000'),
                'condition': 'EXCELLENT',
                'city': 'DOUALA'
            },
            {
                'title': 'Robe Africaine Wax Taille M',
                'description': 'Magnifique robe en tissu wax authentique, taille M. Portée seulement 2 fois pour des événements. Parfaite pour cérémonies et sorties. Très bon état.',
                'price': Decimal('25000'),
                'condition': 'EXCELLENT',
                'city': 'YAOUNDE'
            },
            {
                'title': 'MacBook Air M1 13" 256GB',
                'description': 'MacBook Air avec puce M1, 8GB RAM, 256GB SSD. Acheté en 2023, utilisé pour les études. Performances excellentes, autonomie incroyable. Avec chargeur.',
                'price': Decimal('850000'),
                'condition': 'BON',
                'city': 'DOUALA'
            },
            {
                'title': 'Réfrigérateur Samsung 350L',
                'description': 'Réfrigérateur combiné Samsung 350L, fonctionne parfaitement. Classe énergétique A+, très économique. Cause déménagement. À récupérer sur place.',
                'price': Decimal('180000'),
                'condition': 'BON',
                'city': 'YAOUNDE'
            },
            {
                'title': 'Baskets Nike Air Max 90 Taille 42',
                'description': 'Paire de Nike Air Max 90 taille 42, portée quelques fois. Couleur blanc/noir/rouge. Très confortables, parfaites pour le sport ou casual.',
                'price': Decimal('45000'),
                'condition': 'EXCELLENT',
                'city': 'BAFOUSSAM'
            },
            {
                'title': 'Canapé 3 places en cuir marron',
                'description': 'Canapé 3 places en cuir véritable marron, très confortable. Quelques traces d\'usage mais structure solide. Idéal pour salon. Livraison possible.',
                'price': Decimal('120000'),
                'condition': 'BON',
                'city': 'DOUALA'
            },
            {
                'title': 'Samsung Galaxy S21 Ultra 256GB',
                'description': 'Samsung Galaxy S21 Ultra 256GB, couleur noir fantôme. Écran 120Hz, caméra 108MP exceptionnelle. Protégé depuis l\'achat, état impeccable.',
                'price': Decimal('520000'),
                'condition': 'EXCELLENT',
                'city': 'YAOUNDE'
            },
            {
                'title': 'Machine à laver Whirlpool 7kg',
                'description': 'Machine à laver Whirlpool 7kg, fonctionne parfaitement. Programmes variés, très silencieuse. Cause déménagement. Installation comprise si Douala.',
                'price': Decimal('195000'),
                'condition': 'BON',
                'city': 'DOUALA'
            }
        ]
        
        created_products = []
        
        for i, product_data in enumerate(products_data):
            # Assigner un utilisateur aléatoire comme vendeur
            seller = random.choice(users)
            category = random.choice(categories)
            
            # Créer le slug unique
            slug = f"{product_data['title'].lower().replace(' ', '-')[:50]}-{random.randint(1000, 9999)}"
            
            product = Product.objects.create(
                title=product_data['title'],
                slug=slug,
                description=product_data['description'],
                category=category,
                seller=seller,
                price=product_data['price'],
                condition=product_data['condition'],
                city=product_data['city'],
                source='CLIENT',
                status='ACTIVE',
                is_negotiable=True,
                views_count=random.randint(10, 200),
                likes_count=random.randint(0, 15)
            )
            
            created_products.append(product)
            
            self.stdout.write(
                f'Product {product_data["title"]} created with slug {slug}'
            )