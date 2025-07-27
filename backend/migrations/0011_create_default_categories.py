# Generated manually for default categories

from django.db import migrations
import uuid

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('backend', 'Category')
    
    # Default categories for a vide-grenier platform
    default_categories = [
        {
            'name': 'Électronique',
            'slug': 'electronique',
            'description': 'Téléphones, ordinateurs, tablettes, accessoires électroniques',
            'icon': '📱',
            'is_active': True,
            'order': 1
        },
        {
            'name': 'Vêtements & Mode',
            'slug': 'vetements-mode',
            'description': 'Vêtements, chaussures, accessoires de mode',
            'icon': '👕',
            'is_active': True,
            'order': 2
        },
        {
            'name': 'Maison & Jardin',
            'slug': 'maison-jardin',
            'description': 'Meubles, décoration, jardinage, bricolage',
            'icon': '🏠',
            'is_active': True,
            'order': 3
        },
        {
            'name': 'Sport & Loisirs',
            'slug': 'sport-loisirs',
            'description': 'Équipements sportifs, jeux, loisirs',
            'icon': '⚽',
            'is_active': True,
            'order': 4
        },
        {
            'name': 'Livres & Médias',
            'slug': 'livres-medias',
            'description': 'Livres, CD, DVD, magazines',
            'icon': '📚',
            'is_active': True,
            'order': 5
        },
        {
            'name': 'Automobile',
            'slug': 'automobile',
            'description': 'Voitures, motos, pièces détachées, accessoires',
            'icon': '🚗',
            'is_active': True,
            'order': 6
        },
        {
            'name': 'Beauté & Santé',
            'slug': 'beaute-sante',
            'description': 'Cosmétiques, produits de beauté, santé',
            'icon': '💄',
            'is_active': True,
            'order': 7
        },
        {
            'name': 'Bébés & Enfants',
            'slug': 'bebes-enfants',
            'description': 'Vêtements bébé, jouets, articles pour enfants',
            'icon': '👶',
            'is_active': True,
            'order': 8
        },
        {
            'name': 'Instruments de Musique',
            'slug': 'instruments-musique',
            'description': 'Guitares, pianos, percussions, accessoires',
            'icon': '🎸',
            'is_active': True,
            'order': 9
        },
        {
            'name': 'Art & Collection',
            'slug': 'art-collection',
            'description': 'Tableaux, sculptures, objets de collection',
            'icon': '🎨',
            'is_active': True,
            'order': 10
        },
        {
            'name': 'Outils & Matériel',
            'slug': 'outils-materiel',
            'description': 'Outils de bricolage, matériel professionnel',
            'icon': '🔧',
            'is_active': True,
            'order': 11
        },
        {
            'name': 'Alimentation',
            'slug': 'alimentation',
            'description': 'Produits alimentaires, boissons, épices',
            'icon': '🍎',
            'is_active': True,
            'order': 12
        },
        {
            'name': 'Services',
            'slug': 'services',
            'description': 'Services divers, prestations, cours',
            'icon': '🛠️',
            'is_active': True,
            'order': 13
        },
        {
            'name': 'Autres',
            'slug': 'autres',
            'description': 'Autres articles non classés',
            'icon': '📦',
            'is_active': True,
            'order': 14
        }
    ]
    
    for cat_data in default_categories:
        Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'id': uuid.uuid4(),
                'name': cat_data['name'],
                'description': cat_data['description'],
                'icon': cat_data['icon'],
                'is_active': cat_data['is_active'],
                'order': cat_data['order']
            }
        )

def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('backend', 'Category')
    Category.objects.filter(slug__in=[
        'electronique', 'vetements-mode', 'maison-jardin', 'sport-loisirs',
        'livres-medias', 'automobile', 'beaute-sante', 'bebes-enfants',
        'instruments-musique', 'art-collection', 'outils-materiel',
        'alimentation', 'services', 'autres'
    ]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_advanced_wallet_chat_features'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ] 