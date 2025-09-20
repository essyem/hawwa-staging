"""Add cost_currency to InvoiceItem

Generated manually for development tests.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financial', '0006_accountingcategory_is_cogs_invoiceitem_cost_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='cost_currency',
            field=models.CharField(default='QAR', max_length=10, verbose_name='Cost Currency'),
        ),
    ]
