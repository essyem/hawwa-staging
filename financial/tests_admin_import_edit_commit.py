from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from io import BytesIO, TextIOWrapper
import csv
from decimal import Decimal
from datetime import date

from .models import Invoice, InvoiceItem
from services.models import Service, ServiceCategory


class AdminImportEditCommitTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(email='admin@ex', password='pass')
        self.client.force_login(self.admin_user)

        cat = ServiceCategory.objects.create(name='C', description='x', slug='c')
        svc = Service.objects.create(name='S', description='d', price=Decimal('10.00'), cost=Decimal('5.00'), duration='01:00:00', category=cat, slug='s')
        self.inv = Invoice.objects.create(invoice_number='I-IMPORT', customer=self.admin_user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
        self.item = InvoiceItem.objects.create(invoice=self.inv, service=svc, description='Line1', quantity=1, unit_price=Decimal('10.00'))

    def test_edit_preview_row_and_commit_updates_db(self):
        url = reverse('admin:financial_invoiceitem_import_costs')
        # Create CSV where invoice matches but description is wrong; we'll edit description in preview
        output = BytesIO()
        text_out = TextIOWrapper(output, encoding='utf-8', write_through=True)
        writer = csv.DictWriter(text_out, fieldnames=['invoice_number', 'description', 'cost_amount', 'cost_currency'])
        writer.writeheader()
        writer.writerow({'invoice_number': 'I-IMPORT', 'description': 'TypoLine', 'cost_amount': '9.00', 'cost_currency': 'QAR'})
        text_out.flush()
        output.seek(0)

        resp = self.client.post(url, {'csv_file': output}, follow=True)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8')
        self.assertIn('Commit Import', body)

        # Extract rows_count and prepare edited per-row data: set description to correct 'Line1'
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.content, 'html.parser')
        rows_count = int(soup.find('input', {'name': 'rows_count'})['value'])
        # Build per-row form data to submit
        post_data = {'rows_count': rows_count}
        # For the first row, set description to matching value and cost
        post_data['row_invoice_0'] = 'I-IMPORT'
        post_data['row_description_0'] = 'Line1'
        post_data['row_cost_0'] = '9.00'
        post_data['row_currency_0'] = 'QAR'

        resp2 = self.client.post(url, post_data, follow=True)
        self.assertEqual(resp2.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.cost_amount, Decimal('9.00'))
