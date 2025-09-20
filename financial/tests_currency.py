from django.test import TestCase
from decimal import Decimal
from datetime import date
from django.utils import timezone

from .models import CurrencyRate, AccountingCategory, Invoice, InvoiceItem
from services.models import Service, ServiceCategory
from django.contrib.auth import get_user_model
from .services.reports import profit_and_loss


class CurrencyConversionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='ccy@example.com', password='password')
        cat = ServiceCategory.objects.create(name='Cat', description='x', slug='cat')
        self.svc = Service.objects.create(name='S', description='d', price=Decimal('100.00'), cost=Decimal('50.00'), duration=timezone.timedelta(hours=1), category=cat, slug='s')
        self.cogs = AccountingCategory.objects.create(name='COGS', code='COGS', is_cogs=True)

        # Create an invoice with a cost recorded in USD (simulate)
        self.inv = Invoice.objects.create(invoice_number='C-1', customer=self.user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        item = InvoiceItem.objects.create(invoice=self.inv, service=self.svc, description='Item', quantity=1, unit_price=Decimal('100.00'), cost_amount=Decimal('50.00'), cost_currency='USD', category=self.cogs)

        # Add a rate USD -> QAR of 3.64
        CurrencyRate.objects.create(from_currency='USD', to_currency='QAR', rate=Decimal('3.64000000'), valid_from=date.today())

    def test_convert_and_pl(self):
        start = date.today().replace(day=1)
        end = date.today()
        pl = profit_and_loss(start, end, base_currency='QAR')
        # revenue should be 100 (invoice currency unchanged), costs should be 50 USD -> 182.00 QAR
        self.assertEqual(pl['revenue'], Decimal('100.00'))
        # Allow small quantization; expect 50 * 3.64 = 182.00
        self.assertEqual(pl['costs'], Decimal('182.00'))
        # Gross profit = 100 - 182 = -82
        self.assertEqual(pl['gross_profit'], Decimal('-82.00'))
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date

from .models import CurrencyRate, AccountingCategory
from .services.reports import profit_and_loss
from financial.models import Invoice, InvoiceItem


class CurrencyConversionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='conv@example.com', password='password')
        # create a COGS category
        self.cogs = AccountingCategory.objects.create(name='COGS', code='COGS', is_cogs=True)
        # create a simple rate: 1 USD = 3 QAR
        CurrencyRate.objects.create(from_currency='USD', to_currency='QAR', rate=Decimal('3.0'), valid_from=date(2020,1,1))

    def test_convert_and_pl(self):
        inv = Invoice.objects.create(invoice_number='CCY-1', customer=self.user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        # invoice sold in USD with cost recorded as USD on item
        InvoiceItem.objects.create(invoice=inv, description='Import', quantity=1, unit_price=Decimal('100.00'), cost_amount=Decimal('30.00'), cost_currency='USD', category=self.cogs)

        start = date.today().replace(day=1)
        end = date.today()
        pl = profit_and_loss(start, end, base_currency='QAR')
        # revenue 100, costs converted 30 USD -> 90 QAR
        self.assertEqual(pl['revenue'], Decimal('100.00'))
        self.assertEqual(pl['costs'], Decimal('90.00'))