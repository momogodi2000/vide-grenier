# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0018_add_order_missing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='loyalty_level',
            field=models.CharField(
                choices=[
                    ('BRONZE', 'Bronze'),
                    ('SILVER', 'Silver'),
                    ('GOLD', 'Gold'),
                    ('PLATINUM', 'Platinum'),
                    ('DIAMOND', 'Diamond')
                ],
                default='BRONZE',
                max_length=20
            ),
        ),
    ]
