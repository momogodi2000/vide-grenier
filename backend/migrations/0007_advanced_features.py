# Generated migration for VGK advanced features

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_alter_newslettersubscriber_options_and_more'),
    ]

    operations = [
        # ============= AI & RECOMMENDATION SYSTEM =============
        migrations.CreateModel(
            name='UserBehavior',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action_type', models.CharField(choices=[('VIEW', 'Product View'), ('LIKE', 'Product Like'), ('SEARCH', 'Search'), ('PURCHASE', 'Purchase'), ('CART_ADD', 'Add to Cart'), ('SHARE', 'Share Product'), ('CONTACT_SELLER', 'Contact Seller')], max_length=20)),
                ('session_id', models.CharField(max_length=100)),
                ('duration', models.PositiveIntegerField(default=0)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='behaviors', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.product')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.category')),
            ],
            options={
                'db_table': 'user_behaviors',
            },
        ),
        
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('preferred_categories', models.JSONField(default=list)),
                ('price_range_min', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('price_range_max', models.DecimalField(decimal_places=2, default=100000, max_digits=10)),
                ('preferred_conditions', models.JSONField(default=list)),
                ('preferred_cities', models.JSONField(default=list)),
                ('shopping_patterns', models.JSONField(default=dict)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_preferences',
            },
        ),
        
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('recommendation_type', models.CharField(choices=[('COLLABORATIVE', 'Collaborative Filtering'), ('CONTENT_BASED', 'Content-Based'), ('TRENDING', 'Trending Products'), ('SIMILAR_USERS', 'Similar Users'), ('CROSS_SELL', 'Cross-Sell'), ('UPSELL', 'Upsell')], max_length=20)),
                ('confidence_score', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('reason', models.TextField(blank=True)),
                ('is_clicked', models.BooleanField(default=False)),
                ('is_purchased', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.product')),
            ],
            options={
                'db_table': 'product_recommendations',
            },
        ),
        
        # ============= ENHANCED SHOPPING EXPERIENCE =============
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_carts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'shopping_carts',
            },
        ),
        
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='backend.shoppingcart')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.product')),
            ],
            options={
                'db_table': 'cart_items',
            },
        ),
        
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(default='Ma liste de souhaits', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('is_default', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'wishlists',
            },
        ),
        
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('notes', models.TextField(blank=True)),
                ('priority', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('price_alert_threshold', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('wishlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='backend.wishlist')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.product')),
            ],
            options={
                'db_table': 'wishlist_items',
            },
        ),
        
        # ============= SOCIAL COMMERCE =============
        migrations.CreateModel(
            name='UserFollow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL)),
                ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_follows',
            },
        ),
        
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('overall_rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('quality_rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('seller_rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('delivery_rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('pros', models.JSONField(default=list)),
                ('cons', models.JSONField(default=list)),
                ('is_verified_purchase', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('helpful_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='enhanced_review', to='backend.order')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enhanced_reviews', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enhanced_reviews', to='backend.product')),
            ],
            options={
                'db_table': 'product_reviews_enhanced',
            },
        ),
        
        migrations.CreateModel(
            name='ReviewMedia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('media_type', models.CharField(choices=[('IMAGE', 'Image'), ('VIDEO', 'Video')], max_length=10)),
                ('file', models.FileField(upload_to='reviews/media/')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='backend.productreview')),
            ],
            options={
                'db_table': 'review_media',
                'ordering': ['order'],
            },
        ),
        
        migrations.CreateModel(
            name='SocialPost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('post_type', models.CharField(choices=[('PRODUCT_SHOWCASE', 'Product Showcase'), ('UNBOXING', 'Unboxing'), ('REVIEW', 'Review'), ('COLLECTION', 'Collection'), ('TIP', 'Tip/Advice')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('tags', models.JSONField(default=list)),
                ('is_featured', models.BooleanField(default=False)),
                ('likes_count', models.PositiveIntegerField(default=0)),
                ('comments_count', models.PositiveIntegerField(default=0)),
                ('shares_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_posts', to=settings.AUTH_USER_MODEL)),
                ('products', models.ManyToManyField(blank=True, related_name='social_posts', to='backend.product')),
            ],
            options={
                'db_table': 'social_posts',
                'ordering': ['-created_at'],
            },
        ),
        
        # ============= ADVANCED STAFF FEATURES =============
        migrations.CreateModel(
            name='StaffTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('task_type', models.CharField(choices=[('STOCK_RECEIVE', 'Stock Reception'), ('INVENTORY_COUNT', 'Inventory Count'), ('ORDER_PICKUP', 'Order Pickup'), ('CUSTOMER_SERVICE', 'Customer Service'), ('CLEANING', 'Cleaning/Maintenance'), ('REPORTING', 'Reporting')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM', max_length=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=15)),
                ('due_date', models.DateTimeField()),
                ('estimated_duration', models.PositiveIntegerField(help_text='Estimated duration in minutes')),
                ('actual_duration', models.PositiveIntegerField(blank=True, null=True)),
                ('completion_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_tasks', to=settings.AUTH_USER_MODEL)),
                ('pickup_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='backend.pickuppoint')),
            ],
            options={
                'db_table': 'staff_tasks',
                'ordering': ['due_date', '-priority'],
            },
        ),
        
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('movement_type', models.CharField(choices=[('RECEIVE', 'Stock Received'), ('PICK', 'Order Picked'), ('RETURN', 'Return'), ('DAMAGE', 'Damage Report'), ('ADJUSTMENT', 'Inventory Adjustment'), ('TRANSFER', 'Transfer Between Points')], max_length=15)),
                ('quantity_change', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('batch_id', models.CharField(blank=True, max_length=50)),
                ('location_from', models.CharField(blank=True, max_length=100)),
                ('location_to', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_movements', to='backend.product')),
                ('pickup_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_movements', to='backend.pickuppoint')),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_movements', to=settings.AUTH_USER_MODEL)),
                ('reference_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.order')),
            ],
            options={
                'db_table': 'inventory_movements',
                'ordering': ['-created_at'],
            },
        ),
        
        migrations.CreateModel(
            name='StaffPerformance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('tasks_completed', models.PositiveIntegerField(default=0)),
                ('orders_processed', models.PositiveIntegerField(default=0)),
                ('customer_rating', models.FloatField(default=0.0)),
                ('efficiency_score', models.FloatField(default=0.0)),
                ('punctuality_score', models.FloatField(default=0.0)),
                ('inventory_accuracy', models.FloatField(default=0.0)),
                ('notes', models.TextField(blank=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_records', to=settings.AUTH_USER_MODEL)),
                ('pickup_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_records', to='backend.pickuppoint')),
            ],
            options={
                'db_table': 'staff_performance',
            },
        ),
        
        # ============= SMART NOTIFICATIONS =============
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('notification_type', models.CharField(choices=[('PRICE_DROP', 'Price Drop Alert'), ('BACK_IN_STOCK', 'Back in Stock'), ('NEW_SIMILAR', 'New Similar Product'), ('SELLER_UPDATE', 'Seller Update'), ('RECOMMENDATION', 'AI Recommendation'), ('PROMOTION', 'Promotion'), ('REMINDER', 'Reminder'), ('MILESTONE', 'Achievement/Milestone')], max_length=20)),
                ('title_template', models.CharField(max_length=200)),
                ('message_template', models.TextField()),
                ('email_subject_template', models.CharField(blank=True, max_length=200)),
                ('email_body_template', models.TextField(blank=True)),
                ('sms_template', models.CharField(blank=True, max_length=160)),
                ('trigger_conditions', models.JSONField(default=dict)),
                ('target_audience', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'notification_templates',
            },
        ),
        
        migrations.CreateModel(
            name='SmartNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('delivery_method', models.CharField(choices=[('IN_APP', 'In-App'), ('EMAIL', 'Email'), ('SMS', 'SMS'), ('PUSH', 'Push Notification'), ('WHATSAPP', 'WhatsApp')], max_length=10)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('data', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('DELIVERED', 'Delivered'), ('READ', 'Read'), ('CLICKED', 'Clicked'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('scheduled_for', models.DateTimeField()),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('clicked_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='smart_notifications', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='backend.notificationtemplate')),
            ],
            options={
                'db_table': 'smart_notifications',
                'ordering': ['-scheduled_for'],
            },
        ),
        
        # ============= ADVANCED PAYMENTS =============
        migrations.CreateModel(
            name='EscrowPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('FUNDED', 'Funded'), ('RELEASED_TO_SELLER', 'Released to Seller'), ('REFUNDED_TO_BUYER', 'Refunded to Buyer'), ('DISPUTED', 'Disputed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('funded_at', models.DateTimeField(blank=True, null=True)),
                ('release_date', models.DateTimeField()),
                ('released_at', models.DateTimeField(blank=True, null=True)),
                ('dispute_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='escrow_payment', to='backend.order')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escrow_payments_as_buyer', to=settings.AUTH_USER_MODEL)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escrow_payments_as_seller', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'escrow_payments',
            },
        ),
        
        migrations.CreateModel(
            name='InstallmentPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('down_payment', models.DecimalField(decimal_places=2, max_digits=10)),
                ('number_of_installments', models.PositiveIntegerField()),
                ('installment_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('interest_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='installment_plan', to='backend.order')),
            ],
            options={
                'db_table': 'installment_plans',
            },
        ),
        
        migrations.CreateModel(
            name='InstallmentPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('installment_number', models.PositiveIntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('OVERDUE', 'Overdue'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('payment_reference', models.CharField(blank=True, max_length=100)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='backend.installmentplan')),
            ],
            options={
                'db_table': 'installment_payments',
                'ordering': ['installment_number'],
            },
        ),
        
        # ============= ADD INDEXES =============
        migrations.AddIndex(
            model_name='userbehavior',
            index=models.Index(fields=['user', 'action_type', 'created_at'], name='user_behaviors_user_action_created_idx'),
        ),
        migrations.AddIndex(
            model_name='userbehavior',
            index=models.Index(fields=['product', 'action_type'], name='user_behaviors_product_action_idx'),
        ),
        
        # ============= ADD UNIQUE CONSTRAINTS =============
        migrations.AddConstraint(
            model_name='productrecommendation',
            constraint=models.UniqueConstraint(fields=['user', 'product', 'recommendation_type'], name='unique_user_product_recommendation'),
        ),
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product'),
        ),
        migrations.AddConstraint(
            model_name='wishlistitem',
            constraint=models.UniqueConstraint(fields=['wishlist', 'product'], name='unique_wishlist_product'),
        ),
        migrations.AddConstraint(
            model_name='userfollow',
            constraint=models.UniqueConstraint(fields=['follower', 'following'], name='unique_user_follow'),
        ),
        migrations.AddConstraint(
            model_name='staffperformance',
            constraint=models.UniqueConstraint(fields=['staff_member', 'date'], name='unique_staff_performance_date'),
        ),
        migrations.AddConstraint(
            model_name='installmentpayment',
            constraint=models.UniqueConstraint(fields=['plan', 'installment_number'], name='unique_plan_installment'),
        ),
    ] 