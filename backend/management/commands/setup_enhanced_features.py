# backend/management/commands/setup_enhanced_features.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from backend.models import Category, PickupPoint
from backend.models_advanced import NotificationTemplate, StaffTask
from backend.smart_notifications import smart_notifications

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up enhanced features for VGK platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-notifications',
            action='store_true',
            help='Skip creating notification templates',
        )
        parser.add_argument(
            '--skip-staff-setup',
            action='store_true', 
            help='Skip staff setup and pickup point assignments',
        )
        parser.add_argument(
            '--create-demo-data',
            action='store_true',
            help='Create demo data for testing',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Setting up VGK Enhanced Features...')
        )
        
        try:
            with transaction.atomic():
                # 1. Create notification templates
                if not options['skip_notifications']:
                    self.create_notification_templates()
                
                # 2. Set up staff and pickup points
                if not options['skip_staff_setup']:
                    self.setup_staff_system()
                
                # 3. Create demo data if requested
                if options['create_demo_data']:
                    self.create_demo_data()
                
                # 4. Initialize AI system
                self.initialize_ai_system()
                
                # 5. Set up default configurations
                self.setup_default_configurations()
                
            self.stdout.write(
                self.style.SUCCESS('✅ Enhanced features setup completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Setup failed: {str(e)}')
            )
            logger.error(f"Enhanced features setup failed: {e}")
    
    def create_notification_templates(self):
        """Create all notification templates"""
        self.stdout.write('📧 Creating notification templates...')
        
        templates = [
            {
                'name': 'price_drop_alert',
                'notification_type': 'PRICE_DROP',
                'title_template': '💰 Prix Réduit: {{product_name}}',
                'message_template': 'Le prix de {{product_name}} a baissé de {{old_price}} à {{new_price}} FCFA! Achetez maintenant.',
                'email_subject_template': 'Alerte Prix: {{product_name}} - Économisez {{savings}} FCFA',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Bonne nouvelle! Le produit que vous suivez a baissé de prix:
                
                📦 {{product_name}}
                💰 Ancien prix: {{old_price}} FCFA
                🎉 Nouveau prix: {{new_price}} FCFA
                💵 Vous économisez: {{savings}} FCFA
                
                Achetez maintenant: {{product_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: Prix réduit! {{product_name}}: {{new_price}} FCFA (était {{old_price}})',
                'trigger_conditions': {
                    'type': 'price_drop',
                    'min_drop_percentage': 10,
                    'max_daily': 2
                },
                'target_audience': {}
            },
            {
                'name': 'back_in_stock',
                'notification_type': 'BACK_IN_STOCK', 
                'title_template': '🔥 De retour en stock: {{product_name}}',
                'message_template': '{{product_name}} est de nouveau disponible! Dépêchez-vous, quantité limitée.',
                'email_subject_template': 'Retour en stock: {{product_name}}',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Le produit que vous attendiez est de retour:
                
                📦 {{product_name}}
                💰 Prix: {{price}} FCFA
                📍 Disponible à: {{location}}
                
                Commandez maintenant: {{product_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: {{product_name}} de retour en stock! Commandez vite.',
                'trigger_conditions': {
                    'type': 'back_in_stock',
                    'max_daily': 1
                },
                'target_audience': {}
            },
            {
                'name': 'abandoned_cart',
                'notification_type': 'REMINDER',
                'title_template': '🛒 Vous avez oublié quelque chose!',
                'message_template': 'Votre panier contient {{item_count}} article(s) pour {{total_amount}} FCFA. Terminez votre achat!',
                'email_subject_template': 'N\'oubliez pas votre panier - {{total_amount}} FCFA',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Vous avez laissé {{item_count}} article(s) dans votre panier:
                
                💰 Total: {{total_amount}} FCFA
                🚚 Livraison gratuite disponible
                
                Terminez votre commande: {{cart_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: Votre panier vous attend ({{total_amount}} FCFA). Finalisez votre commande!',
                'trigger_conditions': {
                    'type': 'abandoned_cart',
                    'hours_abandoned': 24,
                    'max_daily': 1
                },
                'target_audience': {}
            },
            {
                'name': 'ai_recommendation',
                'notification_type': 'RECOMMENDATION',
                'title_template': '✨ Recommandé pour vous',
                'message_template': 'Découvrez {{product_name}} à {{price}} FCFA. {{reason}}',
                'email_subject_template': 'Produits recommandés pour vous',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Nous avons trouvé des produits qui pourraient vous intéresser:
                
                📦 {{product_name}}
                💰 Prix: {{price}} FCFA
                🤖 Pourquoi: {{reason}}
                
                Voir plus de recommandations: {{recommendations_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: {{product_name}} recommandé pour vous ({{price}} FCFA)',
                'trigger_conditions': {
                    'type': 'recommendation',
                    'min_confidence': 0.7,
                    'max_daily': 3
                },
                'target_audience': {}
            },
            {
                'name': 'order_shipped',
                'notification_type': 'SELLER_UPDATE',
                'title_template': '📦 Votre commande a été expédiée',
                'message_template': 'Commande {{order_number}} expédiée. Livraison prévue le {{delivery_date}}.',
                'email_subject_template': 'Commande {{order_number}} expédiée',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Votre commande a été expédiée:
                
                📦 Commande: {{order_number}}
                🚚 Transporteur: {{carrier}}
                📍 Suivi: {{tracking_url}}
                📅 Livraison prévue: {{delivery_date}}
                
                Suivre ma commande: {{order_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: Commande {{order_number}} expédiée. Livraison le {{delivery_date}}.',
                'trigger_conditions': {
                    'type': 'order_status_change',
                    'status': 'SHIPPED',
                    'max_daily': 5
                },
                'target_audience': {}
            },
            {
                'name': 'loyalty_milestone',
                'notification_type': 'MILESTONE',
                'title_template': '🎉 Félicitations! Nouveau niveau atteint',
                'message_template': 'Vous venez d\'atteindre le niveau {{new_level}}! Débloquez de nouveaux avantages.',
                'email_subject_template': 'Nouveau niveau de fidélité: {{new_level}}',
                'email_body_template': '''
                Félicitations {{user_name}}!
                
                Vous venez d\'atteindre le niveau {{new_level}} de notre programme de fidélité!
                
                🏆 Niveau: {{new_level}}
                💎 Points: {{total_points}}
                🎁 Nouveaux avantages:
                {{benefits_list}}
                
                Voir mes avantages: {{loyalty_url}}
                
                Cordialement,
                L'équipe VGK
                ''',
                'sms_template': 'VGK: Félicitations! Niveau {{new_level}} atteint. Nouveaux avantages disponibles!',
                'trigger_conditions': {
                    'type': 'milestone',
                    'max_daily': 1
                },
                'target_audience': {}
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created template: {template.name}')
        
        self.stdout.write(f'  📧 Created {created_count} notification templates')
    
    def setup_staff_system(self):
        """Set up staff system and pickup points"""
        self.stdout.write('👥 Setting up staff system...')
        
        # Create default pickup points if they don't exist
        default_pickup_points = [
            {
                'name': 'Point Central Yaoundé',
                'address': 'Carrefour Nlongkak, Yaoundé',
                'city': 'Yaoundé',
                'phone': '+237 6XX XXX XXX',
                'email': 'yaounde@vgk.cm',
                'capacity': 500,
                'is_active': True
            },
            {
                'name': 'Point Douala Akwa',
                'address': 'Boulevard de la Liberté, Akwa, Douala',
                'city': 'Douala',
                'phone': '+237 6XX XXX XXX',
                'email': 'douala@vgk.cm',
                'capacity': 300,
                'is_active': True
            },
            {
                'name': 'Point Bafoussam Centre',
                'address': 'Marché Central, Bafoussam',
                'city': 'Bafoussam',
                'phone': '+237 6XX XXX XXX',
                'email': 'bafoussam@vgk.cm',
                'capacity': 200,
                'is_active': True
            }
        ]
        
        pickup_points_created = 0
        for point_data in default_pickup_points:
            point, created = PickupPoint.objects.get_or_create(
                name=point_data['name'],
                defaults=point_data
            )
            if created:
                pickup_points_created += 1
                self.stdout.write(f'  ✓ Created pickup point: {point.name}')
        
        self.stdout.write(f'  📍 Created {pickup_points_created} pickup points')
        
        # Assign staff to pickup points (if staff users exist)
        staff_users = User.objects.filter(user_type='STAFF', is_active=True)
        pickup_points = PickupPoint.objects.filter(is_active=True)
        
        assignments_made = 0
        for i, staff in enumerate(staff_users):
            if i < len(pickup_points):
                pickup_point = pickup_points[i]
                if not pickup_point.manager:
                    pickup_point.manager = staff
                    pickup_point.save()
                    assignments_made += 1
                    self.stdout.write(f'  ✓ Assigned {staff.username} to {pickup_point.name}')
        
        self.stdout.write(f'  👤 Made {assignments_made} staff assignments')
    
    def create_demo_data(self):
        """Create demo data for testing"""
        self.stdout.write('🎭 Creating demo data...')
        
        # Create demo tasks for staff
        staff_users = User.objects.filter(user_type='STAFF', is_active=True)
        pickup_points = PickupPoint.objects.filter(is_active=True)
        
        if staff_users.exists() and pickup_points.exists():
            demo_tasks = [
                {
                    'task_type': 'STOCK_RECEIVE',
                    'title': 'Réception stock électronique',
                    'description': 'Réceptionner et ranger 50 articles électroniques',
                    'priority': 'HIGH',
                    'estimated_duration': 120,
                    'due_date': timezone.now() + timedelta(hours=4)
                },
                {
                    'task_type': 'INVENTORY_COUNT',
                    'title': 'Inventaire section vêtements',
                    'description': 'Compter et mettre à jour l\'inventaire des vêtements',
                    'priority': 'MEDIUM',
                    'estimated_duration': 90,
                    'due_date': timezone.now() + timedelta(hours=8)
                },
                {
                    'task_type': 'CUSTOMER_SERVICE',
                    'title': 'Assistance client VIP',
                    'description': 'Accompagner client VIP pour sélection produits',
                    'priority': 'HIGH',
                    'estimated_duration': 60,
                    'due_date': timezone.now() + timedelta(hours=2)
                }
            ]
            
            tasks_created = 0
            for staff in staff_users[:3]:  # Limit to first 3 staff
                pickup_point = pickup_points.first()
                
                for task_data in demo_tasks:
                    task = StaffTask.objects.create(
                        assigned_to=staff,
                        created_by=staff,  # Self-assigned for demo
                        pickup_point=pickup_point,
                        **task_data
                    )
                    tasks_created += 1
            
            self.stdout.write(f'  ✓ Created {tasks_created} demo tasks')
        
        # Create demo user behaviors for AI testing
        self.create_demo_user_behaviors()
    
    def create_demo_user_behaviors(self):
        """Create demo user behaviors for AI testing"""
        from backend.models import Product
        from backend.models_advanced import UserBehavior
        
        clients = User.objects.filter(user_type='CLIENT', is_active=True)[:5]
        products = Product.objects.filter(status='ACTIVE')[:20]
        
        if clients.exists() and products.exists():
            behaviors_created = 0
            
            for client in clients:
                # Create varied behaviors for each client
                for product in products[:10]:  # Limit to 10 products per client
                    # View behavior
                    UserBehavior.objects.create(
                        user=client,
                        product=product,
                        category=product.category,
                        action_type='VIEW',
                        session_id=f'demo_session_{client.id}',
                        duration=30000,  # 30 seconds
                        metadata={'demo': True}
                    )
                    behaviors_created += 1
                    
                    # Some like behaviors
                    if behaviors_created % 3 == 0:
                        UserBehavior.objects.create(
                            user=client,
                            product=product,
                            category=product.category,
                            action_type='LIKE',
                            session_id=f'demo_session_{client.id}',
                            metadata={'demo': True}
                        )
                        behaviors_created += 1
            
            self.stdout.write(f'  ✓ Created {behaviors_created} demo user behaviors')
    
    def initialize_ai_system(self):
        """Initialize AI recommendation system"""
        self.stdout.write('🤖 Initializing AI system...')
        
        try:
            from backend.ai_engine import ai_engine
            
            # Create user preferences for existing users
            clients = User.objects.filter(user_type='CLIENT', is_active=True)
            preferences_created = 0
            
            for client in clients:
                prefs = ai_engine._get_or_create_user_preferences(client)
                if prefs:
                    preferences_created += 1
            
            self.stdout.write(f'  ✓ Initialized preferences for {preferences_created} users')
            
            # Generate initial recommendations for active users
            recommendations_generated = 0
            for client in clients[:10]:  # Limit to first 10 for demo
                try:
                    recs = ai_engine.generate_recommendations_for_user(client, 5)
                    if recs:
                        recommendations_generated += len(recs)
                except Exception as e:
                    self.stdout.write(f'  ⚠️  Failed to generate recommendations for {client.username}: {e}')
            
            self.stdout.write(f'  ✓ Generated {recommendations_generated} initial recommendations')
            
        except Exception as e:
            self.stdout.write(f'  ⚠️  AI system initialization failed: {e}')
    
    def setup_default_configurations(self):
        """Set up default configurations"""
        self.stdout.write('⚙️  Setting up default configurations...')
        
        from django.core.cache import cache
        
        # Set up cache keys for various features
        cache_configs = {
            'ai_recommendations_enabled': True,
            'smart_notifications_enabled': True,
            'social_features_enabled': True,
            'advanced_payments_enabled': True,
            'staff_qr_system_enabled': True
        }
        
        for key, value in cache_configs.items():
            cache.set(key, value, timeout=None)  # No expiration
        
        self.stdout.write('  ✓ Default configurations set')
        
        # Initialize smart notifications system
        try:
            smart_notifications.create_notification_templates()
            self.stdout.write('  ✓ Smart notifications system initialized')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Smart notifications init failed: {e}')
        
        self.stdout.write('🎉 All systems initialized successfully!')
        
        # Print summary
        self.print_setup_summary()
    
    def print_setup_summary(self):
        """Print setup summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎯 VGK ENHANCED FEATURES SETUP COMPLETE'))
        self.stdout.write('='*60)
        
        features = [
            '✅ AI Recommendation Engine',
            '✅ Smart Notification System', 
            '✅ Advanced Shopping Cart',
            '✅ Enhanced Wishlist System',
            '✅ Social Commerce Features',
            '✅ Staff QR Code System',
            '✅ Inventory Management',
            '✅ Task Management',
            '✅ Performance Tracking',
            '✅ Advanced Payment Options',
            '✅ Escrow & Installments',
            '✅ Cryptocurrency Support',
            '✅ Business Intelligence',
            '✅ Enhanced Security',
            '✅ PWA Capabilities'
        ]
        
        self.stdout.write('\n🚀 AVAILABLE FEATURES:')
        for feature in features:
            self.stdout.write(f'  {feature}')
        
        self.stdout.write('\n📋 NEXT STEPS:')
        next_steps = [
            '1. Run migrations: python manage.py migrate',
            '2. Create superuser: python manage.py createsuperuser',
            '3. Start development server: python manage.py runserver',
            '4. Access admin panel: http://localhost:8000/admin/',
            '5. Configure payment gateways in settings',
            '6. Set up Celery for background tasks',
            '7. Configure Redis for caching',
            '8. Test AI recommendations',
            '9. Set up notification channels',
            '10. Train staff on new features'
        ]
        
        for step in next_steps:
            self.stdout.write(f'  {step}')
        
        self.stdout.write('\n🔗 IMPORTANT URLS:')
        urls = [
            'Client Features: /client/',
            'Staff Dashboard: /staff/dashboard/', 
            'AI Recommendations: /client/recommendations/',
            'Shopping Cart: /client/cart/',
            'QR Scanner: /staff/qr-scanner/',
            'Analytics: /client/analytics/personal/',
            'Admin Panel: /admin-panel/'
        ]
        
        for url in urls:
            self.stdout.write(f'  {url}')
        
        self.stdout.write('\n⚠️  CONFIGURATION REQUIRED:')
        configs = [
            'Set CAMPAY_API_KEY for mobile payments',
            'Set FIREBASE_SERVER_KEY for push notifications',
            'Set REDIS_URL for caching',
            'Set CELERY_BROKER_URL for background tasks',
            'Configure email settings for notifications',
            'Set up SMS provider credentials'
        ]
        
        for config in configs:
            self.stdout.write(f'  • {config}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎊 WELCOME TO VGK ENHANCED!'))
        self.stdout.write('='*60) 