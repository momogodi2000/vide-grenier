# Generated by Django 5.2.4 on 2025-07-28 05:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0016_add_review_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='pickup_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='backend.pickuppoint'),
        ),
    ]
