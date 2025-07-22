# backend/management/commands/populate_test_data.py - VERSION CORRIGÉE
"""
Django Management Command pour peupler la base de données avec des données de test
Usage: python manage.py populate_test_data [--clear] [--verbose]
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import random
import json
from datetime import datetime, timedelta
from faker import Faker

from backend.models import (
    User, Category, Product, ProductImage, Order, Payment, Review,
    Chat, Message, Favorite, SearchHistory, Notification, AdminStock,
    PickupPoint, Analytics
)

# Initialiser Faker en français
fake = Faker('fr_FR')

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de test réalistes pour le Cameroun'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Vide les tables avant de les remplir',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé',
        )
        parser.add_argument(
            '--categories',
            type=int,
            default=20,  # Réduit pour éviter trop de catégories
            help='Nombre de catégories principales à créer (défaut: 20)',
        )
        parser.add_argument(
            '--products',
            type=int,
            default=100,  # Réduit pour le test initial
            help='Nombre de produits à créer (défaut: 100)',
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=50,  # Réduit pour le test initial
            help='Nombre de commandes à créer (défaut: 50)',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        
        # Vérifier qu'il y a des utilisateurs
        if not User.objects.filter(user_type='CLIENT').exists():
            raise CommandError(
                'Aucun utilisateur CLIENT trouvé. '
                'Vous devez d\'abord créer des utilisateurs avec: '
                'python manage.py create_test_users'
            )
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Suppression des données existantes...'))
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('🚀 Début du peuplement des données de test'))
        
        with transaction.atomic():
            try:
                # Ordre d'insertion respectant les dépendances
                self.create_categories()
                self.create_pickup_points()
                self.create_products(options['products'])
                self.create_admin_stock()
                self.create_orders(options['orders'])
                self.create_payments()
                self.create_reviews()
                self.create_chats_and_messages()
                self.create_favorites()
                self.create_search_history()
                self.create_notifications()
                self.create_analytics()
                
                self.stdout.write(self.style.SUCCESS('✅ Données de test créées avec succès!'))
                self.display_summary()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erreur: {e}'))
                if self.verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())
                raise CommandError(f'Échec du peuplement: {e}')

    def clear_data(self):
        """Supprime toutes les données existantes sauf les utilisateurs"""
        models_to_clear = [
            Analytics, Notification, SearchHistory, Favorite, Message, Chat,
            Review, Payment, Order, AdminStock, ProductImage, Product,
            PickupPoint, Category
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            if self.verbose:
                self.stdout.write(f'  Supprimé {count} {model._meta.verbose_name_plural}')

    def create_categories(self):
        """Crée les catégories principales et sous-catégories camerounaises"""
        self.stdout.write('📂 Création des catégories...')
        
        # Catégories principales simplifiées
        main_categories = [
            {'name': 'Électronique', 'icon': '📱', 'desc': 'Smartphones, ordinateurs, électroménager'},
            {'name': 'Mode & Beauté', 'icon': '👗', 'desc': 'Vêtements, chaussures, cosmétiques'},
            {'name': 'Maison & Jardin', 'icon': '🏠', 'desc': 'Meubles, décoration, jardinage'},
            {'name': 'Véhicules', 'icon': '🚗', 'desc': 'Voitures, motos, pièces détachées'},
            {'name': 'Sports & Loisirs', 'icon': '⚽', 'desc': 'Équipements sportifs, jeux, livres'},
            {'name': 'Enfants & Bébés', 'icon': '👶', 'desc': 'Vêtements enfants, jouets, puériculture'},
            {'name': 'Services', 'icon': '💼', 'desc': 'Services divers'},
            {'name': 'Immobilier', 'icon': '🏘️', 'desc': 'Locations, ventes, terrains'},
            {'name': 'Agriculture', 'icon': '🌾', 'desc': 'Produits agricoles, outils'},
            {'name': 'Artisanat', 'icon': '🎨', 'desc': 'Art traditionnel, objets culturels'},
        ]
        
        # Sous-catégories simplifiées
        subcategories = {
            'Électronique': ['Smartphones', 'Ordinateurs', 'TV & Audio', 'Électroménager'],
            'Mode & Beauté': ['Vêtements Femme', 'Vêtements Homme', 'Chaussures', 'Cosmétiques'],
            'Maison & Jardin': ['Meubles', 'Décoration', 'Jardinage', 'Bricolage'],
            'Véhicules': ['Voitures', 'Motos', 'Vélos', 'Pièces Auto'],
            'Sports & Loisirs': ['Football', 'Basketball', 'Livres', 'Jeux'],
            'Enfants & Bébés': ['Vêtements Bébé', 'Jouets', 'Poussettes', 'Chaussures'],
            'Services': ['Cours', 'Réparation', 'Transport', 'Événementiel'],
            'Immobilier': ['Appartements', 'Maisons', 'Bureaux', 'Terrains'],
            'Agriculture': ['Fruits & Légumes', 'Céréales', 'Outils', 'Semences'],
            'Artisanat': ['Sculptures', 'Masques', 'Bijoux', 'Textiles']
        }
        
        created_categories = {}
        
        # Créer les catégories principales
        for cat_data in main_categories:
            category = Category.objects.create(
                name=cat_data['name'],
                slug=slugify(cat_data['name']),
                description=cat_data['desc'],
                icon=cat_data['icon'],
                is_active=True,
                order=len(created_categories)
            )
            created_categories[cat_data['name']] = category
            
            if self.verbose:
                self.stdout.write(f'  ✅ Catégorie créée: {category.name}')
        
        # Créer les sous-catégories
        for parent_name, subs in subcategories.items():
            parent = created_categories[parent_name]
            for i, sub_name in enumerate(subs):
                sub_category = Category.objects.create(
                    name=sub_name,
                    slug=slugify(f"{parent_name}-{sub_name}"),
                    description=f"Sous-catégorie de {parent_name}",
                    parent=parent,
                    is_active=True,
                    order=i
                )
                
                if self.verbose:
                    self.stdout.write(f'    ↳ Sous-catégorie: {sub_category.name}')
        
        self.stdout.write(f'📂 {Category.objects.count()} catégories créées')

    def create_pickup_points(self):
        """Crée des points de retrait dans les principales villes du Cameroun"""
        self.stdout.write('📍 Création des points de retrait...')
        
        pickup_points_data = [
            # Douala
            {'name': 'VGK Douala Centre', 'city': 'DOUALA', 'address': 'Rue Joss, près du marché central, Douala', 'phone': '+237670123456'},
            {'name': 'VGK Akwa', 'city': 'DOUALA', 'address': 'Boulevard de la Liberté, Akwa, Douala', 'phone': '+237670123457'},
            # Yaoundé
            {'name': 'VGK Yaoundé Centre', 'city': 'YAOUNDE', 'address': 'Avenue Kennedy, Centre Ville, Yaoundé', 'phone': '+237670123460'},
            {'name': 'VGK Bastos', 'city': 'YAOUNDE', 'address': 'Quartier Bastos, près de l\'ambassade de France', 'phone': '+237670123462'},
            # Autres villes
            {'name': 'VGK Bafoussam Centre', 'city': 'BAFOUSSAM', 'address': 'Place de l\'indépendance, Bafoussam', 'phone': '+237670123464'},
            {'name': 'VGK Garoua Centre', 'city': 'GAROUA', 'address': 'Grand marché de Garoua', 'phone': '+237670123466'},
            {'name': 'VGK Bamenda Commercial', 'city': 'BAMENDA', 'address': 'Commercial Avenue, Bamenda', 'phone': '+237670123468'},
        ]
        
        # Obtenir des managers (staff users)
        staff_users = list(User.objects.filter(user_type='STAFF'))
        
        for point_data in pickup_points_data:
            opening_hours = {
                'monday': {'open': '08:00', 'close': '18:00'},
                'tuesday': {'open': '08:00', 'close': '18:00'},
                'wednesday': {'open': '08:00', 'close': '18:00'},
                'thursday': {'open': '08:00', 'close': '18:00'},
                'friday': {'open': '08:00', 'close': '18:00'},
                'saturday': {'open': '08:00', 'close': '16:00'},
                'sunday': {'open': '10:00', 'close': '14:00'}
            }
            
            pickup_point = PickupPoint.objects.create(
                name=point_data['name'],
                city=point_data['city'],
                address=point_data['address'],
                phone=point_data['phone'],
                email=f"pickup.{slugify(point_data['name'])}@videgrenier-kamer.com",
                opening_hours=opening_hours,
                capacity=random.randint(50, 200),
                current_stock=random.randint(0, 30),
                manager=random.choice(staff_users) if staff_users else None,
                is_active=True
            )
            
            if self.verbose:
                self.stdout.write(f'  ✅ Point de retrait: {pickup_point.name}')
        
        self.stdout.write(f'📍 {PickupPoint.objects.count()} points de retrait créés')

    def create_products(self, count):
        """Crée des produits réalistes pour le marché camerounais"""
        self.stdout.write(f'📦 Création de {count} produits...')
        
        # Produits populaires au Cameroun avec prix réalistes
        product_data = [
            {'name': 'iPhone 12 Pro Max 128GB', 'cat': 'Smartphones', 'price_range': (400000, 650000)},
            {'name': 'Samsung Galaxy A32', 'cat': 'Smartphones', 'price_range': (120000, 180000)},
            {'name': 'Tecno Spark 7', 'cat': 'Smartphones', 'price_range': (75000, 110000)},
            {'name': 'MacBook Air M1', 'cat': 'Ordinateurs', 'price_range': (700000, 950000)},
            {'name': 'HP Pavilion 15', 'cat': 'Ordinateurs', 'price_range': (350000, 500000)},
            {'name': 'Toyota Corolla 2018', 'cat': 'Voitures', 'price_range': (6000000, 8500000)},
            {'name': 'Honda Accord 2019', 'cat': 'Voitures', 'price_range': (7500000, 10000000)},
            {'name': 'Robe Africaine Traditionnelle', 'cat': 'Vêtements Femme', 'price_range': (15000, 45000)},
            {'name': 'Ensemble Pagne Camerounais', 'cat': 'Vêtements Femme', 'price_range': (25000, 65000)},
            {'name': 'Canapé 3 Places', 'cat': 'Meubles', 'price_range': (150000, 350000)},
            {'name': 'Table à Manger en Bois', 'cat': 'Meubles', 'price_range': (75000, 200000)},
            {'name': 'Vélo VTT', 'cat': 'Vélos', 'price_range': (85000, 200000)},
            {'name': 'Ballon de Football', 'cat': 'Football', 'price_range': (8000, 25000)},
            {'name': 'Console PlayStation 4', 'cat': 'Jeux', 'price_range': (180000, 280000)},
        ]
        
        categories = list(Category.objects.filter(parent__isnull=False))  # Sous-catégories
        users = list(User.objects.filter(user_type='CLIENT'))
        cities = ['DOUALA', 'YAOUNDE', 'BAFOUSSAM', 'GAROUA', 'BAMENDA']
        conditions = ['NEUF', 'EXCELLENT', 'BON', 'CORRECT', 'USAGE']
        
        if not users:
            raise CommandError('Aucun utilisateur CLIENT trouvé')
        
        for i in range(count):
            try:
                # Choisir un template de produit
                template = random.choice(product_data)
                
                # Trouver une catégorie appropriée ou utiliser une aléatoire
                category = None
                for cat in categories:
                    if template['cat'].lower() in cat.name.lower():
                        category = cat
                        break
                if not category:
                    category = random.choice(categories)
                
                seller = random.choice(users)
                
                # Variations du titre
                variations = ['Excellent état', 'Comme neuf', 'Occasion', 'Récent', 'À saisir']
                title = f"{template['name']} - {random.choice(variations)}"
                
                # Prix dans la fourchette appropriée
                min_price, max_price = template['price_range']
                price = Decimal(random.randint(min_price, max_price))
                
                # Description réaliste
                descriptions = [
                    f"Magnifique {template['name']} en excellent état. Utilisé avec précaution.",
                    f"{template['name']} à vendre cause déménagement. Très bien entretenu.",
                    f"Vends {template['name']} urgent. Prix négociable. Inspection possible.",
                    f"{template['name']} de qualité supérieure. Livraison possible sur Douala.",
                    f"Superbe {template['name']} à prix attractif. À saisir rapidement!"
                ]
                
                product = Product.objects.create(
                    title=title[:200],  # Limiter la longueur
                    slug=f"{slugify(title[:50])}-{i}",  # Limiter et ajouter index
                    description=random.choice(descriptions),
                    category=category,
                    seller=seller,
                    price=price,
                    condition=random.choice(conditions),
                    source=random.choice(['CLIENT', 'ADMIN']),
                    status=random.choices(['ACTIVE', 'SOLD', 'RESERVED'], weights=[80, 15, 5])[0],
                    is_negotiable=random.choice([True, True, False]),  # 66% négociables
                    city=random.choice(cities),
                    views_count=random.randint(0, 100),
                    likes_count=random.randint(0, 20),
                    is_featured=random.random() < 0.1,  # 10% featured
                    is_premium=random.random() < 0.05,  # 5% premium
                    expires_at=timezone.now() + timedelta(days=random.randint(30, 90))
                )
                
                # Créer 1-3 images par produit
                for img_idx in range(random.randint(1, 3)):
                    ProductImage.objects.create(
                        product=product,
                        image=f'products/images/placeholder_{random.randint(1, 10)}.jpg',
                        alt_text=f"Image {img_idx + 1} de {product.title}",
                        is_primary=(img_idx == 0),
                        order=img_idx
                    )
                
                if self.verbose and (i + 1) % 20 == 0:
                    self.stdout.write(f'  📦 {i + 1}/{count} produits créés...')
                    
            except Exception as e:
                self.stdout.write(f'  ⚠️  Erreur produit {i}: {e}')
                continue
        
        self.stdout.write(f'📦 {Product.objects.count()} produits créés')

    def create_admin_stock(self):
        """Crée des stocks admin pour certains produits"""
        self.stdout.write('📊 Création des stocks administrateur...')
        
        admin_products = Product.objects.filter(source='ADMIN', status='ACTIVE')[:20]
        cities = ['DOUALA', 'YAOUNDE', 'BAFOUSSAM', 'GAROUA', 'BAMENDA']
        
        for product in admin_products:
            try:
                purchase_price = product.price * Decimal(str(random.uniform(0.6, 0.8)))
                
                AdminStock.objects.create(
                    product=product,
                    sku=f"VGK-{random.randint(100000, 999999)}",
                    quantity=random.randint(1, 3),
                    location=random.choice(cities),
                    shelf_location=f"A{random.randint(1, 5)}-{random.randint(1, 20)}",
                    purchase_price=purchase_price,
                    condition_notes=random.choice([
                        "Produit neuf sous emballage",
                        "Excellent état général",
                        "Quelques rayures mineures",
                        "Emballage légèrement abîmé"
                    ]),
                    warranty_info=random.choice([
                        "Garantie constructeur 2 ans",
                        "Garantie magasin 6 mois",
                        "Sans garantie"
                    ]),
                    status=random.choice(['AVAILABLE', 'AVAILABLE', 'RESERVED'])
                )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur stock admin: {e}')
                continue
        
        self.stdout.write(f'📊 {AdminStock.objects.count()} stocks admin créés')

    def create_orders(self, count):
        """Crée des commandes réalistes"""
        self.stdout.write(f'🛒 Création de {count} commandes...')
        
        products = list(Product.objects.filter(status='ACTIVE'))
        users = list(User.objects.filter(user_type='CLIENT'))
        
        if not products:
            self.stdout.write('⚠️  Aucun produit actif trouvé, création d\'ordre annulée')
            return
        
        if not users:
            self.stdout.write('⚠️  Aucun utilisateur trouvé, création d\'ordre annulée')
            return
        
        statuses = ['PENDING', 'PAID', 'PROCESSING', 'DELIVERED', 'CANCELLED']
        payment_methods = ['CAMPAY', 'ORANGE_MONEY', 'MTN_MONEY', 'CASH_ON_DELIVERY']
        delivery_methods = ['PICKUP', 'DELIVERY']
        
        created_orders = 0
        for i in range(count):
            try:
                product = random.choice(products)
                # 70% avec acheteur, 30% anonyme
                buyer = random.choice(users) if random.random() < 0.7 else None
                
                # Prix avec frais de livraison
                delivery_cost = Decimal(random.randint(1000, 5000))
                total_amount = product.price + delivery_cost
                commission = product.price * Decimal('0.08')  # 8% commission
                
                order = Order.objects.create(
                    buyer=buyer,  # Peut être None pour les commandes anonymes
                    product=product,
                    quantity=1,
                    total_amount=total_amount,
                    commission_amount=commission,
                    delivery_cost=delivery_cost,
                    status=random.choice(statuses),
                    payment_method=random.choice(payment_methods),
                    delivery_method=random.choice(delivery_methods),
                    delivery_address=fake.address() if random.choice([True, False]) else "",
                    pickup_code=f"{random.randint(100000, 999999)}" if random.choice([True, False]) else "",
                    notes=random.choice([
                        "Livraison urgente svp",
                        "Appeler avant livraison", 
                        "Disponible le week-end",
                        ""
                    ]),
                    created_at=fake.date_time_between(
                        start_date='-3m', 
                        end_date='now', 
                        tzinfo=timezone.get_current_timezone()
                    )
                )
                
                # Ajouter delivered_at si livré
                if order.status == 'DELIVERED':
                    order.delivered_at = fake.date_time_between(
                        start_date=order.created_at,
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    )
                    order.save()
                
                created_orders += 1
                
                if self.verbose and created_orders % 10 == 0:
                    self.stdout.write(f'  🛒 {created_orders}/{count} commandes créées...')
                    
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur commande {i}: {e}')
                continue
        
        self.stdout.write(f'🛒 {created_orders} commandes créées')

    def create_payments(self):
        """Crée des paiements pour les commandes"""
        self.stdout.write('💳 Création des paiements...')
        
        orders_without_payment = Order.objects.filter(payment__isnull=True)[:50]
        statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
        
        for order in orders_without_payment:
            try:
                status = 'COMPLETED' if order.status in ['PAID', 'DELIVERED'] else random.choice(statuses)
                
                Payment.objects.create(
                    order=order,
                    payment_reference=f"PAY-{random.randint(1000000, 9999999)}",
                    amount=order.total_amount,
                    status=status,
                    provider_response={
                        'transaction_id': f"TXN-{random.randint(100000, 999999)}",
                        'provider': order.payment_method,
                        'status': status,
                        'timestamp': timezone.now().isoformat()
                    },
                    transaction_id=f"TXN-{random.randint(100000, 999999)}",
                    completed_at=timezone.now() if status == 'COMPLETED' else None
                )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur paiement: {e}')
                continue
        
        self.stdout.write(f'💳 {Payment.objects.count()} paiements créés')

    def create_reviews(self):
        """Crée des avis clients"""
        self.stdout.write('⭐ Création des avis clients...')
        
        # Seulement les commandes avec acheteur ET livrées
        completed_orders = Order.objects.filter(
            status='DELIVERED',
            buyer__isnull=False,  # Seulement les commandes avec acheteur
            review__isnull=True
        )[:30]
        
        positive_comments = [
            "Excellent vendeur, produit conforme à la description!",
            "Livraison rapide, très satisfait de mon achat.",
            "Produit de qualité, je recommande vivement!",
            "Transaction parfaite, vendeur sérieux.",
            "Très bon rapport qualité-prix, merci!"
        ]
        
        negative_comments = [
            "Produit pas exactement comme décrit.",
            "Livraison un peu lente mais produit correct.",
            "Communication difficile avec le vendeur."
        ]
        
        for order in completed_orders:
            try:
                # 80% d'avis positifs
                is_positive = random.random() < 0.8
                base_rating = random.randint(4, 5) if is_positive else random.randint(2, 3)
                
                Review.objects.create(
                    order=order,
                    reviewer=order.buyer,  # On sait qu'il n'est pas None
                    product_quality=max(1, min(5, base_rating + random.randint(-1, 1))),
                    seller_communication=base_rating,
                    delivery_speed=max(1, min(5, base_rating + random.randint(-1, 1))),
                    packaging=base_rating,
                    overall_rating=base_rating,
                    comment=random.choice(positive_comments if is_positive else negative_comments),
                    images=[],
                    is_verified=True,
                    helpful_count=random.randint(0, 5)
                )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur avis: {e}')
                continue
        
        self.stdout.write(f'⭐ {Review.objects.count()} avis créés')

    def create_chats_and_messages(self):
        """Crée des chats et messages entre utilisateurs"""
        self.stdout.write('💬 Création des chats et messages...')
        
        products = list(Product.objects.filter(status='ACTIVE')[:20])
        buyers = list(User.objects.filter(user_type='CLIENT'))
        
        if not products or not buyers:
            self.stdout.write('⚠️  Pas assez de données pour créer des chats')
            return
        
        for product in products[:10]:  # Limiter à 10 chats
            try:
                # Choisir un acheteur différent du vendeur
                available_buyers = [b for b in buyers if b != product.seller]
                if not available_buyers:
                    continue
                    
                buyer = random.choice(available_buyers)
                
                chat = Chat.objects.create(
                    product=product,
                    buyer=buyer,
                    seller=product.seller,
                    is_active=True
                )
                
                # 2-5 messages par chat
                message_templates = [
                    "Bonjour, le produit est-il disponible?",
                    "Oui, il est disponible.",
                    "Quel est l'état exact?",
                    "Le prix est-il négociable?",
                    "Parfait, je suis intéressé!",
                    "Merci pour les infos!"
                ]
                
                for msg_idx in range(random.randint(2, 5)):
                    sender = buyer if msg_idx % 2 == 0 else product.seller
                    
                    Message.objects.create(
                        chat=chat,
                        sender=sender,
                        message_type='TEXT',
                        content=random.choice(message_templates),
                        is_read=random.choice([True, False]),
                        created_at=fake.date_time_between(
                            start_date='-30d', 
                            end_date='now', 
                            tzinfo=timezone.get_current_timezone()
                        )
                    )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur chat: {e}')
                continue
        
        self.stdout.write(f'💬 {Chat.objects.count()} chats et {Message.objects.count()} messages créés')

    def create_favorites(self):
        """Crée des favoris pour les utilisateurs"""
        self.stdout.write('❤️ Création des favoris...')
        
        users = list(User.objects.filter(user_type='CLIENT')[:20])  # Limiter à 20 utilisateurs
        products = list(Product.objects.filter(status='ACTIVE'))
        
        if not users or not products:
            self.stdout.write('⚠️  Pas assez de données pour créer des favoris')
            return
        
        # Chaque utilisateur a 3-8 favoris
        for user in users:
            try:
                num_favorites = random.randint(3, 8)
                # Éviter de dépasser le nombre de produits disponibles
                num_favorites = min(num_favorites, len(products))
                user_products = random.sample(products, num_favorites)
                
                for product in user_products:
                    Favorite.objects.get_or_create(
                        user=user,
                        product=product,
                        defaults={
                            'created_at': fake.date_time_between(
                                start_date='-2m', 
                                end_date='now', 
                                tzinfo=timezone.get_current_timezone()
                            )
                        }
                    )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur favoris pour {user.email}: {e}')
                continue
        
        self.stdout.write(f'❤️ {Favorite.objects.count()} favoris créés')

    def create_search_history(self):
        """Crée l'historique de recherches"""
        self.stdout.write('🔍 Création de l\'historique de recherches...')
        
        search_terms = [
            'iPhone', 'Samsung', 'Toyota', 'Honda', 'Robe',
            'Ordinateur', 'Télévision', 'Canapé', 'Table',
            'Chaussures', 'Montre', 'Vélo', 'Moto', 'Voiture',
            'Appartement', 'Maison', 'Emploi', 'Cours',
            'Fruits', 'Légumes', 'Artisanat'
        ]
        
        users = list(User.objects.filter(user_type='CLIENT'))
        categories = list(Category.objects.all())
        
        for i in range(100):  # 100 recherches
            try:
                user = random.choice(users) if random.random() < 0.6 else None
                search_term = random.choice(search_terms)
                category = random.choice(categories) if random.random() < 0.3 else None
                
                SearchHistory.objects.create(
                    user=user,
                    search_term=search_term,
                    category=category,
                    results_count=random.randint(0, 25),
                    ip_address=fake.ipv4(),
                    created_at=fake.date_time_between(
                        start_date='-2m', 
                        end_date='now', 
                        tzinfo=timezone.get_current_timezone()
                    )
                )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur recherche {i}: {e}')
                continue
        
        self.stdout.write(f'🔍 {SearchHistory.objects.count()} recherches créées')

    def create_notifications(self):
        """Crée des notifications pour les utilisateurs"""
        self.stdout.write('🔔 Création des notifications...')
        
        users = list(User.objects.filter(user_type='CLIENT')[:20])  # Limiter à 20 utilisateurs
        notification_types = ['ORDER', 'PAYMENT', 'MESSAGE', 'REVIEW', 'SYSTEM', 'PROMOTION']
        
        notification_templates = {
            'ORDER': {
                'titles': ['Nouvelle commande', 'Commande confirmée', 'Commande livrée'],
                'messages': [
                    'Votre commande a été confirmée.',
                    'Votre produit a été expédié.',
                    'Votre commande a été livrée.'
                ]
            },
            'PAYMENT': {
                'titles': ['Paiement reçu', 'Paiement confirmé'],
                'messages': [
                    'Votre paiement a été confirmé.',
                    'Paiement en cours de traitement.'
                ]
            },
            'MESSAGE': {
                'titles': ['Nouveau message', 'Réponse reçue'],
                'messages': [
                    'Vous avez reçu un nouveau message.',
                    'Nouvelle réponse à votre message.'
                ]
            },
            'REVIEW': {
                'titles': ['Nouvel avis reçu', 'Avis publié'],
                'messages': [
                    'Vous avez reçu un nouvel avis.',
                    'Votre avis a été publié.'
                ]
            },
            'SYSTEM': {
                'titles': ['Mise à jour', 'Maintenance'],
                'messages': [
                    'Mise à jour système effectuée.',
                    'Maintenance programmée demain.'
                ]
            },
            'PROMOTION': {
                'titles': ['Offre spéciale', 'Promotion'],
                'messages': [
                    'Profitez de 20% de réduction!',
                    'Livraison gratuite ce week-end.'
                ]
            }
        }
        
        for user in users:
            try:
                num_notifications = random.randint(2, 6)
                
                for _ in range(num_notifications):
                    notif_type = random.choice(notification_types)
                    templates = notification_templates[notif_type]
                    
                    title = random.choice(templates['titles'])
                    message = random.choice(templates['messages'])
                    
                    Notification.objects.create(
                        user=user,
                        type=notif_type,
                        title=title,
                        message=message,
                        data={
                            'priority': random.choice(['low', 'medium', 'high']),
                            'category': notif_type.lower()
                        },
                        is_read=random.random() < 0.4,  # 40% lues
                        created_at=fake.date_time_between(
                            start_date='-1m', 
                            end_date='now', 
                            tzinfo=timezone.get_current_timezone()
                        )
                    )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur notifications pour {user.email}: {e}')
                continue
        
        self.stdout.write(f'🔔 {Notification.objects.count()} notifications créées')

    def create_analytics(self):
        """Crée des données d'analytics"""
        self.stdout.write('📈 Création des analytics...')
        
        metric_types = ['PAGE_VIEW', 'PRODUCT_VIEW', 'SEARCH', 'CLICK']
        users = list(User.objects.filter(user_type='CLIENT'))
        products = list(Product.objects.all())
        
        pages = ['/', '/products/', '/categories/', '/dashboard/', '/profile/']
        referrers = ['https://google.com', 'https://facebook.com', '', 'direct']
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
            'Mozilla/5.0 (Android 11; Mobile; rv:90.0)'
        ]
        
        for i in range(200):  # 200 événements analytics
            try:
                metric_type = random.choice(metric_types)
                user = random.choice(users) if random.random() < 0.5 else None
                
                data = {}
                page_url = ""
                
                if metric_type == 'PAGE_VIEW':
                    page_url = f"https://videgrenier-kamer.com{random.choice(pages)}"
                    data = {
                        'page_title': 'Vidé-Grenier Kamer',
                        'duration': random.randint(10, 300)
                    }
                
                elif metric_type == 'PRODUCT_VIEW' and products:
                    product = random.choice(products)
                    page_url = f"https://videgrenier-kamer.com/products/{product.slug}/"
                    data = {
                        'product_id': str(product.id),
                        'product_title': product.title,
                        'category': product.category.name,
                        'price': float(product.price)
                    }
                
                elif metric_type == 'SEARCH':
                    search_terms = ['iPhone', 'Samsung', 'Toyota', 'Robe']
                    data = {
                        'search_term': random.choice(search_terms),
                        'results_count': random.randint(0, 20)
                    }
                
                elif metric_type == 'CLICK':
                    data = {
                        'element_type': random.choice(['button', 'link']),
                        'element_text': random.choice(['Acheter', 'Voir plus', 'Contact'])
                    }
                
                Analytics.objects.create(
                    metric_type=metric_type,
                    user=user,
                    session_id=f"sess_{random.randint(100000, 999999)}",
                    page_url=page_url,
                    referrer=random.choice(referrers),
                    user_agent=random.choice(user_agents),
                    ip_address=fake.ipv4(),
                    data=data,
                    created_at=fake.date_time_between(
                        start_date='-1m', 
                        end_date='now', 
                        tzinfo=timezone.get_current_timezone()
                    )
                )
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f'  ⚠️  Erreur analytics {i}: {e}')
                continue
        
        self.stdout.write(f'📈 {Analytics.objects.count()} événements analytics créés')

    def display_summary(self):
        """Affiche un résumé des données créées"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ DES DONNÉES CRÉÉES'))
        self.stdout.write('='*60)
        
        summary_data = [
            ('👥 Utilisateurs', User.objects.count()),
            ('📂 Catégories', Category.objects.count()),
            ('📦 Produits', Product.objects.count()),
            ('🖼️ Images produits', ProductImage.objects.count()),
            ('🛒 Commandes', Order.objects.count()),
            ('💳 Paiements', Payment.objects.count()),
            ('⭐ Avis clients', Review.objects.count()),
            ('💬 Conversations', Chat.objects.count()),
            ('📨 Messages', Message.objects.count()),
            ('❤️ Favoris', Favorite.objects.count()),
            ('🔍 Recherches', SearchHistory.objects.count()),
            ('🔔 Notifications', Notification.objects.count()),
            ('📊 Stocks admin', AdminStock.objects.count()),
            ('📍 Points de retrait', PickupPoint.objects.count()),
            ('📈 Analytics', Analytics.objects.count()),
        ]
        
        for label, count in summary_data:
            self.stdout.write(f'{label:<20} : {count:>6}')
        
        self.stdout.write('\n' + '='*60)
        
        # Statistiques business
        try:
            total_revenue = sum(
                o.total_amount for o in Order.objects.filter(status='DELIVERED')
            )
            active_products = Product.objects.filter(status='ACTIVE').count()
            completed_orders = Order.objects.filter(status='DELIVERED').count()
            total_orders = Order.objects.count()
            
            self.stdout.write(self.style.SUCCESS('💰 STATISTIQUES BUSINESS'))
            self.stdout.write('-'*60)
            self.stdout.write(f'Chiffre d\'affaires total    : {total_revenue:,.0f} FCFA')
            self.stdout.write(f'Produits actifs            : {active_products}')
            self.stdout.write(f'Commandes livrées          : {completed_orders}')
            if total_orders > 0:
                conversion_rate = (completed_orders / total_orders) * 100
                self.stdout.write(f'Taux de conversion         : {conversion_rate:.1f}%')
        except Exception as e:
            self.stdout.write(f'⚠️  Erreur calcul statistiques: {e}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ DONNÉES DE TEST PRÊTES POUR VGK!'))
        self.stdout.write('🚀 Vous pouvez maintenant tester toutes les fonctionnalités')
        self.stdout.write('='*60)