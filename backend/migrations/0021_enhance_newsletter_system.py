# Generated manually

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0020_add_pickup_point_missing_fields'),
    ]

    operations = [
        # Add new fields to NewsletterSubscriber
        migrations.AddField(
            model_name='newslettersubscriber',
            name='phone',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='newslettersubscriber',
            name='city',
            field=models.CharField(blank=True, choices=[('DOUALA', 'Douala'), ('YAOUNDE', 'Yaoundé'), ('BAMENDA', 'Bamenda'), ('BUEA', 'Buea'), ('KRIBI', 'Kribi'), ('LIMBE', 'Limbé'), ('BERTOUA', 'Bertoua'), ('GAROUA', 'Garoua'), ('MAROUA', 'Maroua'), ('NGAOUNDERE', 'Ngaoundéré'), ('BAFOUSSAM', 'Bafoussam'), ('EBOLOWA', 'Ebolowa'), ('KOUNDJA', 'Koundja'), ('KUMBA', 'Kumba'), ('MBALMAYO', 'Mbalmayo'), ('MEIGANGA', 'Meiganga'), ('NKONGSAMBA', 'Nkongsamba'), ('SANGMELIMA', 'Sangmélima'), ('TIKO', 'Tiko'), ('OTHER', 'Autre')], max_length=20),
        ),
        migrations.AddField(
            model_name='newslettersubscriber',
            name='last_email_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newslettersubscriber',
            name='email_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='newslettersubscriber',
            name='preferences',
            field=models.JSONField(blank=True, default=dict),
        ),
        
        # Create NewsletterCampaign model
        migrations.CreateModel(
            name='NewsletterCampaign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('subject', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('html_content', models.TextField(blank=True)),
                ('campaign_type', models.CharField(choices=[('NEWSLETTER', 'Newsletter générale'), ('PROMOTION', 'Promotion/Offre'), ('ANNOUNCEMENT', 'Annonce importante'), ('PRODUCT_ALERT', 'Alerte produit'), ('EVENT', 'Événement'), ('CUSTOM', 'Campagne personnalisée')], default='NEWSLETTER', max_length=20)),
                ('status', models.CharField(choices=[('DRAFT', 'Brouillon'), ('SCHEDULED', 'Programmée'), ('SENDING', 'En cours d\'envoi'), ('SENT', 'Envoyée'), ('CANCELLED', 'Annulée'), ('FAILED', 'Échouée')], default='DRAFT', max_length=20)),
                ('target_cities', models.JSONField(blank=True, default=list)),
                ('target_user_types', models.JSONField(blank=True, default=list)),
                ('target_loyalty_levels', models.JSONField(blank=True, default=list)),
                ('target_active_users', models.BooleanField(default=True)),
                ('target_new_subscribers', models.BooleanField(default=False)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('total_recipients', models.PositiveIntegerField(default=0)),
                ('sent_count', models.PositiveIntegerField(default=0)),
                ('opened_count', models.PositiveIntegerField(default=0)),
                ('clicked_count', models.PositiveIntegerField(default=0)),
                ('unsubscribed_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='campaigns_created', to='backend.user')),
            ],
            options={
                'db_table': 'newsletter_campaigns',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create NewsletterTemplate model
        migrations.CreateModel(
            name='NewsletterTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('template_type', models.CharField(choices=[('WELCOME', 'Bienvenue'), ('PROMOTION', 'Promotion'), ('NEWSLETTER', 'Newsletter générale'), ('EVENT', 'Événement'), ('CUSTOM', 'Personnalisé')], max_length=20)),
                ('subject_template', models.CharField(max_length=200)),
                ('content_template', models.TextField()),
                ('html_template', models.TextField(blank=True)),
                ('variables', models.JSONField(blank=True, default=dict, help_text='Variables disponibles dans le template')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates_created', to='backend.user')),
            ],
            options={
                'db_table': 'newsletter_templates',
                'ordering': ['name'],
            },
        ),
        
        # Create NewsletterLog model
        migrations.CreateModel(
            name='NewsletterLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('SENT', 'Envoyé'), ('FAILED', 'Échoué'), ('BOUNCED', 'Rebondi'), ('UNSUBSCRIBED', 'Désabonné')], default='PENDING', max_length=20)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('clicked_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='backend.newslettercampaign')),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_logs', to='backend.newslettersubscriber')),
            ],
            options={
                'db_table': 'newsletter_logs',
                'ordering': ['-sent_at'],
            },
        ),
        
        # Create ScheduledNewsletter model
        migrations.CreateModel(
            name='ScheduledNewsletter',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('frequency', models.CharField(choices=[('DAILY', 'Quotidien'), ('WEEKLY', 'Hebdomadaire'), ('MONTHLY', 'Mensuel'), ('CUSTOM', 'Personnalisé')], default='WEEKLY', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('next_send_date', models.DateTimeField()),
                ('last_sent_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scheduled_newsletters_created', to='backend.user')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_newsletters', to='backend.newslettertemplate')),
            ],
            options={
                'db_table': 'scheduled_newsletters',
                'ordering': ['next_send_date'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='newslettersubscriber',
            index=models.Index(fields=['email'], name='newsletter_subscribers_email_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettersubscriber',
            index=models.Index(fields=['is_active'], name='newsletter_subscribers_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettersubscriber',
            index=models.Index(fields=['city'], name='newsletter_subscribers_city_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettersubscriber',
            index=models.Index(fields=['subscribed_at'], name='newsletter_subscribers_subscribed_at_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettercampaign',
            index=models.Index(fields=['status'], name='newsletter_campaigns_status_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettercampaign',
            index=models.Index(fields=['campaign_type'], name='newsletter_campaigns_campaign_type_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettercampaign',
            index=models.Index(fields=['scheduled_at'], name='newsletter_campaigns_scheduled_at_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettercampaign',
            index=models.Index(fields=['created_at'], name='newsletter_campaigns_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettertemplate',
            index=models.Index(fields=['template_type'], name='newsletter_templates_template_type_idx'),
        ),
        migrations.AddIndex(
            model_name='newslettertemplate',
            index=models.Index(fields=['is_active'], name='newsletter_templates_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='newsletterlog',
            index=models.Index(fields=['status'], name='newsletter_logs_status_idx'),
        ),
        migrations.AddIndex(
            model_name='newsletterlog',
            index=models.Index(fields=['sent_at'], name='newsletter_logs_sent_at_idx'),
        ),
        migrations.AddIndex(
            model_name='newsletterlog',
            index=models.Index(fields=['campaign', 'subscriber'], name='newsletter_logs_campaign_subscriber_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednewsletter',
            index=models.Index(fields=['is_active'], name='scheduled_newsletters_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednewsletter',
            index=models.Index(fields=['next_send_date'], name='scheduled_newsletters_next_send_date_idx'),
        ),
        migrations.AddIndex(
            model_name='schedulednewsletter',
            index=models.Index(fields=['frequency'], name='scheduled_newsletters_frequency_idx'),
        ),
    ]
