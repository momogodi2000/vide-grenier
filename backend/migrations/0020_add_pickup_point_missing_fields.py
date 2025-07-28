# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0019_add_user_loyalty_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='pickuppoint',
            name='special_hours',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='pickuppoint',
            name='processing_time',
            field=models.PositiveIntegerField(default=24, help_text='Temps de traitement en heures'),
        ),
        migrations.AddField(
            model_name='pickuppoint',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='pickuppoint',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
