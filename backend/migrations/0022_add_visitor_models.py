# Generated manually

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0021_enhance_newsletter_system'),
    ]

    operations = [
        # Create VisitorCart model
        migrations.CreateModel(
            name='VisitorCart',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('session_key', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'visitor_carts_enhanced',
                'ordering': ['-updated_at'],
            },
        ),
        
        # Create VisitorCartItem model
        migrations.CreateModel(
            name='VisitorCartItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='backend.visitorcart')),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_cart_items')),
            ],
            options={
                'db_table': 'visitor_cart_items_enhanced',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create VisitorFavorite model
        migrations.CreateModel(
            name='VisitorFavorite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('session_key', models.CharField(max_length=100)),
                ('visitor_ip', models.GenericIPAddressField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_favorites_enhanced')),
            ],
            options={
                'db_table': 'visitor_favorites_enhanced',
                'unique_together': {('session_key', 'product')},
            },
        ),
        
        # Create VisitorCompare model
        migrations.CreateModel(
            name='VisitorCompare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('session_key', models.CharField(max_length=100)),
                ('visitor_ip', models.GenericIPAddressField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_compares_enhanced')),
            ],
            options={
                'db_table': 'visitor_compares_enhanced',
                'unique_together': {('session_key', 'product')},
            },
        ),
        
        # Create ProductComment model
        migrations.CreateModel(
            name='ProductComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('content', models.TextField()),
                ('visitor_name', models.CharField(max_length=100)),
                ('visitor_email', models.EmailField(max_length=254)),
                ('visitor_ip', models.GenericIPAddressField()),
                ('is_approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_comments_enhanced')),
                ('user', models.ForeignKey(to='backend.User', blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_comments_enhanced')),
            ],
            options={
                'db_table': 'product_comments_enhanced',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create ProductLike model
        migrations.CreateModel(
            name='ProductLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('like_type', models.CharField(choices=[('LIKE', 'J\'aime'), ('DISLIKE', 'Je n\'aime pas')], default='LIKE', max_length=10)),
                ('visitor_ip', models.GenericIPAddressField()),
                ('session_key', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_likes_enhanced')),
                ('user', models.ForeignKey(to='backend.User', blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_likes_enhanced')),
            ],
            options={
                'db_table': 'product_likes_enhanced',
                'unique_together': {('product', 'visitor_ip', 'session_key')},
            },
        ),
        
        # Create ProductReport model
        migrations.CreateModel(
            name='ProductReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('reason', models.CharField(choices=[('INAPPROPRIATE', 'Contenu inapproprié'), ('FAKE', 'Faux produit'), ('SPAM', 'Spam'), ('DUPLICATE', 'Produit en double'), ('OTHER', 'Autre')], max_length=20)),
                ('description', models.TextField()),
                ('visitor_ip', models.GenericIPAddressField()),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('product', models.ForeignKey(to='backend.Product', on_delete=django.db.models.deletion.CASCADE, related_name='visitor_reports_enhanced')),
                ('reporter', models.ForeignKey(to='backend.User', blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_reports_enhanced')),
            ],
            options={
                'db_table': 'product_reports_enhanced',
                'ordering': ['-created_at'],
            },
        ),
    ] 