from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from io import BytesIO, TextIOWrapper
import csv
from decimal import Decimal
from datetime import date

from .models import Invoice, InvoiceItem
from services.models import Service, ServiceCategory


class AdminImportUnmatchedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(email='admin@ex', password='pass')
        self.client.force_login(self.admin_user)

        cat = ServiceCategory.objects.create(name='C', description='x', slug='c')
        svc = Service.objects.create(name='S', description='d', price=Decimal('10.00'), cost=Decimal('5.00'), duration='01:00:00', category=cat, slug='s')
        self.inv = Invoice.objects.create(invoice_number='I-IMPORT', customer=self.admin_user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        self.item = InvoiceItem.objects.create(invoice=self.inv, service=svc, description='Line1', quantity=1, unit_price=Decimal('10.00'))

    def test_unmatched_export_available(self):
        url = reverse('admin:financial_invoiceitem_import_costs')
        # Prepare CSV with missing invoice to force unmatched
        output = BytesIO()
        text_out = TextIOWrapper(output, encoding='utf-8', write_through=True)
        writer = csv.DictWriter(text_out, fieldnames=['invoice_number', 'description', 'cost_amount', 'cost_currency'])
        writer.writeheader()
        writer.writerow({'invoice_number': '', 'description': 'NoInvoice', 'cost_amount': '7.50', 'cost_currency': 'QAR'})
        text_out.flush()
        output.seek(0)

        resp = self.client.post(url, {'csv_file': output}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Commit using the payload
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.content, 'html.parser')
        payload_input = soup.find('input', {'name': 'commit_payload'})
        self.assertIsNotNone(payload_input)
        payload = payload_input['value']

        resp2 = self.client.post(url, {'commit_payload': payload}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        # Now request unmatched CSV (GET with param)
        resp3 = self.client.get(url + '?download_unmatched=1')
        # Should return a CSV
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(resp3['Content-Type'], 'text/csv')
        body = resp3.content.decode('utf-8')
        self.assertIn('invoice,reason', body)
