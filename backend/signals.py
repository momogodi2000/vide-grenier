

# backend/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, Payment, Review, Product, Notification, AdminStock
from .utils import send_sms_notification, create_system_notification
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


@receiver(post_save, sender=User)
def user_created_welcome(sender, instance, created, **kwargs):
    """Envoyer un message de bienvenue lors de la création d'un utilisateur"""
    if created and instance.user_type == 'CLIENT':
        # Créer une notification de bienvenue
        create_system_notification(
            user=instance,
            title='Bienvenue sur Vidé-Grenier Kamer!',
            message='Votre compte a été créé avec succès. Explorez nos fonctionnalités et commencez à acheter ou vendre dès maintenant!',
            notification_type='SYSTEM'
        )
        
        # Envoyer un SMS de bienvenue
        welcome_sms = f"Bienvenue {instance.first_name} sur Vidé-Grenier Kamer! Votre compte est créé. Explorez et commencez à économiser dès maintenant!"
        send_sms_notification(instance.phone, welcome_sms)


@receiver(post_save, sender=Order)
def order_status_notifications(sender, instance, created, **kwargs):
    """Gérer les notifications lors des changements de statut de commande"""
    if created:
        # Notifier le vendeur d'une nouvelle commande
        seller = instance.product.seller
        
        # Handle visitor orders (buyer can be None)
        if instance.buyer:
            buyer_name = instance.buyer.get_full_name()
        else:
            buyer_name = instance.visitor_name or "Visiteur anonyme"
        
        create_system_notification(
            user=seller,
            title='Nouvelle commande reçue!',
            message=f'Vous avez reçu une commande pour "{instance.product.title}" de {buyer_name}',
            notification_type='ORDER',
            data={'order_id': str(instance.id)}
        )
        
        # SMS au vendeur
        sms_seller = f"Nouvelle commande VGK: {instance.product.title} - {instance.total_amount} FCFA. Commande #{instance.order_number}"
        send_sms_notification(seller.phone, sms_seller)
        
        # Notifier l'acheteur
        create_system_notification(
            user=instance.buyer,
            title='Commande créée avec succès',
            message=f'Votre commande #{instance.order_number} a été créée. Procédez au paiement pour la confirmer.',
            notification_type='ORDER',
            data={'order_id': str(instance.id)}
        )
    
    else:
        # Gérer les changements de statut
        if instance.status == 'PAID':
            # Marquer le produit comme vendu
            instance.product.status = 'SOLD'
            instance.product.save()
            
            # Notifier le vendeur du paiement
            create_system_notification(
                user=instance.product.seller,
                title='Paiement reçu!',
                message=f'Le paiement de {instance.total_amount} FCFA pour "{instance.product.title}" a été confirmé.',
                notification_type='PAYMENT',
                data={'order_id': str(instance.id)}
            )
        
        elif instance.status == 'DELIVERED':
            # Notifier l'acheteur de la livraison
            create_system_notification(
                user=instance.buyer,
                title='Commande livrée',
                message=f'Votre commande #{instance.order_number} a été livrée. N\'oubliez pas de laisser un avis!',
                notification_type='ORDER',
                data={'order_id': str(instance.id)}
            )
            
            # Libérer les fonds au vendeur (simulé)
            seller_amount = instance.total_amount - instance.commission_amount
            create_system_notification(
                user=instance.product.seller,
                title='Fonds libérés',
                message=f'Votre vente est confirmée! {seller_amount} FCFA seront transférés dans 24h.',
                notification_type='PAYMENT',
                data={'order_id': str(instance.id), 'amount': str(seller_amount)}
            )


@receiver(post_save, sender=Payment)
def payment_status_notifications(sender, instance, created, **kwargs):
    """Gérer les notifications de paiement"""
    if not created and instance.status == 'COMPLETED':
        # Mettre à jour le statut de la commande
        instance.order.status = 'PAID'
        instance.order.save()
        
        # Notifier l'acheteur
        create_system_notification(
            user=instance.order.buyer,
            title='Paiement confirmé',
            message=f'Votre paiement de {instance.amount} FCFA a été confirmé avec succès.',
            notification_type='PAYMENT',
            data={'payment_id': str(instance.id)}
        )
    
    elif not created and instance.status == 'FAILED':
        # Libérer le produit
        instance.order.product.status = 'ACTIVE'
        instance.order.product.save()
        
        # Notifier l'acheteur de l'échec
        create_system_notification(
            user=instance.order.buyer,
            title='Échec du paiement',
            message=f'Le paiement pour la commande #{instance.order.order_number} a échoué. Veuillez réessayer.',
            notification_type='PAYMENT',
            data={'payment_id': str(instance.id)}
        )


@receiver(post_save, sender=Review)
def review_notifications(sender, instance, created, **kwargs):
    """Gérer les notifications d'avis"""
    if created:
        # Notifier le vendeur du nouvel avis
        seller = instance.order.product.seller
        create_system_notification(
            user=seller,
            title='Nouvel avis reçu',
            message=f'Vous avez reçu un avis {instance.overall_rating}★ pour "{instance.order.product.title}"',
            notification_type='REVIEW',
            data={'review_id': str(instance.id)}
        )
        
        # Mettre à jour le score de confiance du vendeur
        update_seller_trust_score(seller)


def update_seller_trust_score(seller):
    """Mettre à jour le score de confiance basé sur les avis"""
    from django.db.models import Avg
    
    avg_rating = Review.objects.filter(
        order__product__seller=seller
    ).aggregate(Avg('overall_rating'))['overall_rating__avg']
    
    if avg_rating:
        # Formule: Score de base (70) + bonus basé sur la note moyenne
        base_score = 70
        rating_bonus = (avg_rating - 3) * 10  # +/- 10 points par étoile au-dessus/en-dessous de 3
        review_count_bonus = min(10, Review.objects.filter(order__product__seller=seller).count())
        
        new_score = base_score + rating_bonus + review_count_bonus
        seller.trust_score = max(0, min(100, int(new_score)))
        seller.save()


@receiver(post_save, sender=Product)
def product_created_notifications(sender, instance, created, **kwargs):
    """Notifications lors de la création de produit"""
    if created and instance.source == 'CLIENT':
        # Notifier les admins pour validation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admins = User.objects.filter(user_type='ADMIN', is_active=True)
        for admin in admins:
            create_system_notification(
                user=admin,
                title='Nouveau produit à valider',
                message=f'Le produit "{instance.title}" de {instance.seller.get_full_name()} nécessite une validation.',
                notification_type='SYSTEM',
                data={'product_id': str(instance.id)}
            )


@receiver(pre_save, sender=Product)
def product_status_change(sender, instance, **kwargs):
    """Détecter les changements de statut de produit"""
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            
            # Si le produit passe de DRAFT à ACTIVE
            if old_instance.status == 'DRAFT' and instance.status == 'ACTIVE':
                create_system_notification(
                    user=instance.seller,
                    title='Produit validé et publié',
                    message=f'Votre produit "{instance.title}" a été validé et est maintenant visible sur la plateforme.',
                    notification_type='SYSTEM',
                    data={'product_id': str(instance.id)}
                )
            
            # Si le produit est suspendu
            elif old_instance.status != 'SUSPENDED' and instance.status == 'SUSPENDED':
                create_system_notification(
                    user=instance.seller,
                    title='Produit suspendu',
                    message=f'Votre produit "{instance.title}" a été temporairement suspendu. Contactez le support pour plus d\'informations.',
                    notification_type='SYSTEM',
                    data={'product_id': str(instance.id)}
                )
        except Product.DoesNotExist:
            pass

# ============= WALLET & COMMISSION SIGNALS =============

@receiver(post_save, sender=Order)
def handle_order_wallet_transactions(sender, instance, created, **kwargs):
    """Handle wallet transactions and commissions when orders are processed"""
    from .models_advanced import Wallet, Transaction, Commission
    from decimal import Decimal
    
    # Only process when order is paid
    if instance.status == 'PAID' and hasattr(instance, 'product') and instance.product.seller:
        seller = instance.product.seller
        
        # Get or create seller wallet
        seller_wallet, created = Wallet.objects.get_or_create(user=seller)
        
        # Calculate commission (10%)
        commission_rate = Decimal('0.10')
        total_amount = instance.total_amount
        commission_amount = total_amount * commission_rate
        seller_amount = total_amount - commission_amount
        
        # Create commission record
        commission_record, created = Commission.objects.get_or_create(
            order=instance,
            defaults={
                'seller': seller,
                'base_amount': total_amount,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'seller_amount': seller_amount,
                'is_paid': False,
            }
        )
        
        if created or not commission_record.is_paid:
            # Add funds to seller wallet (after commission)
            seller_wallet.add_funds(
                seller_amount,
                f"Vente produit: {instance.product.title} (Commande #{instance.order_number})"
            )
            
            # Mark commission as paid
            commission_record.is_paid = True
            commission_record.paid_at = timezone.now()
            commission_record.save()
            
            # Create transaction for commission tracking
            Transaction.objects.create(
                wallet=seller_wallet,
                transaction_type='CREDIT',
                amount=seller_amount,
                description=f"Vente: {instance.product.title}",
                source='SALE',
                reference_id=str(instance.id),
                status='COMPLETED'
            )


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """Create wallet for new users"""
    from .models_advanced import Wallet, OnlineStatus, ChatSettings
    
    if created and instance.user_type == 'CLIENT':
        # Create wallet for clients
        Wallet.objects.get_or_create(user=instance)
        
        # Create online status
        OnlineStatus.objects.get_or_create(user=instance)
        
        # Create chat settings
        ChatSettings.objects.get_or_create(user=instance)


@receiver(post_save, sender='backend.PrivateMessage')
def update_chat_timestamp(sender, instance, created, **kwargs):
    """Update chat timestamp when new message is sent"""
    if created:
        chat = instance.private_chat
        chat.last_message_at = instance.created_at
        chat.save(update_fields=['last_message_at'])


@receiver(post_save, sender='backend.GroupChatMessage')
def update_group_chat_timestamp(sender, instance, created, **kwargs):
    """Update group chat timestamp when new message is sent"""
    if created:
        group_chat = instance.group_chat
        group_chat.updated_at = instance.created_at
        group_chat.save(update_fields=['updated_at'])


# ============= COMMISSION HANDLING =============

def process_commission_payment(commission_id):
    """Process commission payment to admin account"""
    from .models_advanced import Commission, Transaction, Wallet
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        commission = Commission.objects.get(id=commission_id)
        
        # Get admin user
        admin_user = User.objects.filter(user_type='ADMIN').first()
        if not admin_user:
            return False
        
        # Get or create admin wallet
        admin_wallet, created = Wallet.objects.get_or_create(user=admin_user)
        
        # Add commission to admin wallet
        admin_wallet.add_funds(
            commission.commission_amount,
            f"Commission vente: {commission.order.product.title} (10%)"
        )
        
        # Create commission transaction record
        Transaction.objects.create(
            wallet=admin_wallet,
            transaction_type='COMMISSION',
            amount=commission.commission_amount,
            description=f"Commission 10% - Commande #{commission.order.order_number}",
            source='COMMISSION',
            reference_id=str(commission.order.id),
            status='COMPLETED'
        )
        
        return True
        
    except Exception as e:
        print(f"Error processing commission: {e}")
        return False


# ============= AUTOMATIC WALLET CREATION =============

@receiver(post_save, sender=User)
def setup_user_financial_accounts(sender, instance, created, **kwargs):
    """Set up financial accounts for new users"""
    from .models_advanced import Wallet, OnlineStatus, ChatSettings
    
    if created:
        # Create wallet for all user types (clients get active wallets, others get tracking wallets)
        Wallet.objects.get_or_create(
            user=instance,
            defaults={
                'balance': Decimal('0.00'),
                'is_frozen': False if instance.user_type == 'CLIENT' else True,
            }
        )
        
        # Create online status for real-time features
        OnlineStatus.objects.get_or_create(
            user=instance,
            defaults={'status': 'OFFLINE'}
        )
        
        # Create chat settings
        ChatSettings.objects.get_or_create(
            user=instance,
            defaults={
                'notification_preference': 'ALL',
                'email_notifications': True,
                'show_online_status': True,
            }
        )
