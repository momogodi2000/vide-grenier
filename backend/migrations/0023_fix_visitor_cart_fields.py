# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0022_add_visitor_models'),
    ]

    operations = [
        # Add missing fields to VisitorCart
        migrations.AddField(
            model_name='visitorcart',
            name='visitor_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='visitor_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='visitor_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='visitor_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='delivery_method',
            field=models.CharField(choices=[('PICKUP', 'Retrait en point'), ('DELIVERY', 'Livraison à domicile')], default='PICKUP', max_length=20),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='payment_option',
            field=models.CharField(choices=[('CAMPAY_DELIVERY', 'Campay + Livraison (2000 FCFA)'), ('WHATSAPP_PICKUP', 'WhatsApp + Retrait sur place'), ('WHATSAPP_NEGOTIATION', 'WhatsApp + Négociation')], default='WHATSAPP_PICKUP', max_length=30),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='delivery_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='pickup_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.pickuppoint'),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='whatsapp_preferred',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='email_preferred',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='sms_preferred',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='special_instructions',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='ai_recommendations_shown',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='behavior_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='is_abandoned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='abandoned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='visitorcart',
            name='last_activity',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add missing fields to VisitorCartItem
        migrations.AddField(
            model_name='visitorcartitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, default=0),
        ),
        migrations.AddField(
            model_name='visitorcartitem',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcartitem',
            name='special_requests',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcartitem',
            name='added_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        
        # Add missing fields to VisitorFavorite (removed duplicate visitor_ip)
        migrations.AddField(
            model_name='visitorfavorite',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorfavorite',
            name='priority',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='visitorfavorite',
            name='price_alert_threshold',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        
        # Add missing fields to VisitorCompare (removed duplicate visitor_ip)
        migrations.AddField(
            model_name='visitorcompare',
            name='comparison_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='visitorcompare',
            name='preference_score',
            field=models.IntegerField(default=0),
        ),
        
        # Add missing fields to ProductComment (removed duplicate visitor fields)
        migrations.AddField(
            model_name='productcomment',
            name='session_key',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='rating',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='backend.productcomment'),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='is_spam',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='moderation_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='likes_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='dislikes_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='productcomment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add missing fields to ProductLike (removed duplicate visitor_ip and session_key)
        migrations.AddField(
            model_name='productlike',
            name='reason',
            field=models.TextField(blank=True),
        ),
        
        # Add missing fields to ProductReport (removed duplicate visitor_ip and resolved_at)
        migrations.AddField(
            model_name='productreport',
            name='reporter_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='productreport',
            name='reporter_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='productreport',
            name='session_key',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='productreport',
            name='report_type',
            field=models.CharField(choices=[('FAKE', 'Produit contrefait'), ('INAPPROPRIATE', 'Contenu inapproprié'), ('MISLEADING', 'Description trompeuse'), ('OVERPRICED', 'Prix excessif'), ('SPAM', 'Spam/Publicité'), ('DUPLICATE', 'Annonce dupliquée'), ('BROKEN', 'Produit défectueux'), ('DANGEROUS', 'Produit dangereux'), ('ILLEGAL', 'Produit illégal'), ('OTHER', 'Autre')], max_length=20),
        ),
        migrations.AddField(
            model_name='productreport',
            name='evidence',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='productreport',
            name='priority',
            field=models.CharField(choices=[('LOW', 'Faible'), ('MEDIUM', 'Moyenne'), ('HIGH', 'Élevée'), ('URGENT', 'Urgente')], default='MEDIUM', max_length=10),
        ),
        migrations.AddField(
            model_name='productreport',
            name='status',
            field=models.CharField(choices=[('PENDING', 'En attente'), ('REVIEWING', 'En cours d\'examen'), ('RESOLVED', 'Résolu'), ('DISMISSED', 'Rejeté'), ('ESCALATED', 'Escaladé')], default='PENDING', max_length=20),
        ),
        migrations.AddField(
            model_name='productreport',
            name='admin_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='productreport',
            name='resolved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_visitor_reports', to='backend.user'),
        ),
        migrations.AddField(
            model_name='productreport',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='visitorcart',
            index=models.Index(fields=['visitor_phone'], name='visitor_carts_enhanced_visitor_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='visitorcart',
            index=models.Index(fields=['is_active', 'created_at'], name='visitor_carts_enhanced_is_active_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='visitorcart',
            index=models.Index(fields=['is_abandoned', 'abandoned_at'], name='visitor_carts_enhanced_is_abandoned_abandoned_at_idx'),
        ),
    ] 