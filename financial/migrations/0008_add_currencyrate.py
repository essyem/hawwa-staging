"""Add CurrencyRate model

Generated manually for development tests.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financial', '0007_invoiceitem_cost_currency'),
    ]

    operations = [
        migrations.CreateModel(
            name='CurrencyRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_currency', models.CharField(max_length=10, verbose_name='From Currency')),
                ('to_currency', models.CharField(max_length=10, verbose_name='To Currency')),
                ('rate', models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Rate')),
                ('valid_from', models.DateField(default=models.timezone.now, verbose_name='Valid From')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='Valid To')),
            ],
            options={'verbose_name': 'Currency Rate', 'verbose_name_plural': 'Currency Rates'},
        ),
        migrations.AddIndex(
            model_name='currencyrate',
            index=models.Index(fields=['from_currency', 'to_currency', 'valid_from'], name='financial_curr_from_to_idx'),
        ),
    ]
