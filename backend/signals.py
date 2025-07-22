

# backend/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, Payment, Review, Product, Notification, AdminStock
from .utils import send_sms_notification, create_system_notification

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
        create_system_notification(
            user=seller,
            title='Nouvelle commande reçue!',
            message=f'Vous avez reçu une commande pour "{instance.product.title}" de {instance.buyer.get_full_name()}',
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
