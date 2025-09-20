"""Add cost field to Service model

Generated manually for development tests.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='cost',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=2, verbose_name='Cost'),
        ),
    ]
