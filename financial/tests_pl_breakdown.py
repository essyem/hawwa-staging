from django.test import TestCase
from decimal import Decimal
from datetime import date
from django.utils import timezone

from .models import AccountingCategory, Invoice, InvoiceItem
from services.models import Service, ServiceCategory
from django.contrib.auth import get_user_model
from .services.reports import profit_and_loss


class PLBreakdownTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='plb@example.com', password='password')
        cat1 = AccountingCategory.objects.create(name='Services', code='SVC', is_cogs=False)
        cat2 = AccountingCategory.objects.create(name='Products', code='PRD', is_cogs=True)

        s_cat = ServiceCategory.objects.create(name='SCat', description='x', slug='scat')
        svc = Service.objects.create(name='Svc1', description='d', price=Decimal('200.00'), cost=Decimal('80.00'), duration=timezone.timedelta(hours=1), category=s_cat, slug='svc1')

        today = date.today()
        inv = Invoice.objects.create(invoice_number='PB-1', customer=self.user, invoice_date=today, due_date=today, billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        # revenue in Services (non-COGS)
        InvoiceItem.objects.create(invoice=inv, service=svc, description='Service Fee', quantity=1, unit_price=Decimal('200.00'), category=cat1)
        # revenue in Products (COGS) with cost
        InvoiceItem.objects.create(invoice=inv, service=svc, description='Product', quantity=1, unit_price=Decimal('1000.00'), cost_amount=Decimal('600.00'), category=cat2)

    def test_breakdown(self):
        start = date.today().replace(day=1)
        end = date.today()
        pl = profit_and_loss(start, end, base_currency='QAR')
        breakdown = {b['category_code']: b for b in pl['breakdown']}
        # Services category revenue 200, costs 0
        self.assertIn('SVC', breakdown)
        self.assertEqual(breakdown['SVC']['revenue'], Decimal('200.00'))
        self.assertEqual(breakdown['SVC']['costs'], Decimal('0.00'))
        # Products category revenue 1000, costs 600
        self.assertIn('PRD', breakdown)
        self.assertEqual(breakdown['PRD']['revenue'], Decimal('1000.00'))
        self.assertEqual(breakdown['PRD']['costs'], Decimal('600.00'))
        # gross for PRD is 400, gross margin pct = 400/1000 * 100 = 40
        self.assertEqual(breakdown['PRD']['gross'], Decimal('400.00'))
        self.assertEqual(breakdown['PRD']['gross_margin_pct'], Decimal('40'))
