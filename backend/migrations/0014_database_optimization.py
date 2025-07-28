# Generated manually for database optimization

from django.db import migrations, models
import django.contrib.postgres.indexes


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_add_product_approval_fields'),
    ]

    operations = [
        # Add search vector field for full-text search (PostgreSQL only)
        migrations.AddField(
            model_name='product',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(blank=True, null=True),
        ),
        
        # User indexes
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['phone'], name='users_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type', 'is_active'], name='users_type_active_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['city', 'is_active'], name='users_city_active_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['created_at'], name='users_created_idx'),
        ),
        
        # Product indexes
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['status', 'created_at'], name='products_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['seller', 'status'], name='products_seller_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'status'], name='products_category_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['city', 'status'], name='products_city_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['price'], name='products_price_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['condition', 'status'], name='products_condition_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_featured', 'status'], name='products_featured_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['views_count'], name='products_views_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['likes_count'], name='products_likes_idx'),
        ),
        
        # Order indexes (only for existing fields)
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_number'], name='orders_number_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['buyer', 'status'], name='orders_buyer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['product', 'status'], name='orders_product_status_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', 'created_at'], name='orders_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_method', 'status'], name='orders_payment_status_idx'),
        ),
        
        # Payment indexes
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_reference'], name='payments_reference_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'created_at'], name='payments_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['transaction_id'], name='payments_transaction_idx'),
        ),
        
        # Review indexes
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['reviewer', 'created_at'], name='reviews_reviewer_created_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['order', 'created_at'], name='reviews_order_created_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['overall_rating'], name='reviews_rating_idx'),
        ),
        
        # Category indexes
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['name'], name='categories_name_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['is_active'], name='categories_active_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['order'], name='categories_order_idx'),
        ),
        
        # PickupPoint indexes
        migrations.AddIndex(
            model_name='pickuppoint',
            index=models.Index(fields=['city'], name='pickup_city_idx'),
        ),
        migrations.AddIndex(
            model_name='pickuppoint',
            index=models.Index(fields=['is_active'], name='pickup_active_idx'),
        ),
        
        # AdminStock indexes
        migrations.AddIndex(
            model_name='adminstock',
            index=models.Index(fields=['product'], name='stock_product_idx'),
        ),
        migrations.AddIndex(
            model_name='adminstock',
            index=models.Index(fields=['location'], name='stock_location_idx'),
        ),
        
        # Notification indexes
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='notifications_user_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['type', 'created_at'], name='notifications_type_created_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='notifications_created_idx'),
        ),
        
        # Chat indexes
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['buyer', 'is_active'], name='chats_buyer_active_idx'),
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['seller', 'is_active'], name='chats_seller_active_idx'),
        ),
        migrations.AddIndex(
            model_name='chat',
            index=models.Index(fields=['product', 'is_active'], name='chats_product_active_idx'),
        ),
        
        # Message indexes
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['chat', 'created_at'], name='messages_chat_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender', 'created_at'], name='messages_sender_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['is_read', 'created_at'], name='messages_read_created_idx'),
        ),
        
        # Favorite indexes
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['user', 'created_at'], name='favorites_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['product', 'created_at'], name='favorites_product_created_idx'),
        ),
        
        # SearchHistory indexes
        migrations.AddIndex(
            model_name='searchhistory',
            index=models.Index(fields=['user', 'created_at'], name='search_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='searchhistory',
            index=models.Index(fields=['search_term'], name='search_term_idx'),
        ),
    ] 