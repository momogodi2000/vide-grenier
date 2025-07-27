# Generated manually for product slug generation

from django.db import migrations
from django.utils.text import slugify

def generate_product_slugs(apps, schema_editor):
    Product = apps.get_model('backend', 'Product')
    
    for product in Product.objects.all():
        if not product.slug:
            base_slug = slugify(product.title)
            slug = base_slug
            
            # Ensure uniqueness
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            product.slug = slug
            product.save(update_fields=['slug'])

def reverse_generate_slugs(apps, schema_editor):
    # No reverse operation needed - we don't want to delete slugs
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0011_create_default_categories'),
    ]

    operations = [
        migrations.RunPython(generate_product_slugs, reverse_generate_slugs),
    ] 