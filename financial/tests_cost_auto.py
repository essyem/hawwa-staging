from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from financial.models import Invoice, InvoiceItem
from services.models import Service, ServiceCategory

class InvoiceItemCostAutoTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='svc@example.com', password='password')
        # Create a service category and a service with a cost
        cat = ServiceCategory.objects.create(name='TestCat', description='x', slug='testcat')
        self.svc = Service.objects.create(name='TestSvc', description='d', price=Decimal('100.00'), cost=Decimal('60.00'), duration=timedelta(hours=1), category=cat, slug='testsrv')

    def test_auto_populate_cost(self):
        inv = Invoice.objects.create(invoice_number='AUTO-1', customer=self.user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        item = InvoiceItem.objects.create(invoice=inv, service=self.svc, description='Svc', quantity=1, unit_price=Decimal('100.00'))
        self.assertEqual(item.cost_amount, Decimal('60.00'))
