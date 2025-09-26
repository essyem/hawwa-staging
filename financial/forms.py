from django import forms
from django.utils import timezone
from .models import Invoice, Payment, Expense


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'invoice_type', 'status', 'due_date', 'notes', 
                 'billing_name', 'billing_email', 'billing_phone', 'billing_address', 'billing_city']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter any notes for this invoice...'
            }),
            'billing_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer billing name'
            }),
            'billing_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'customer@example.com'
            }),
            'billing_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+974 XXXX XXXX'
            }),
            'billing_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter billing address...'
            }),
            'billing_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Doha'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default due date to 30 days from now for new invoices
        if not self.instance.pk:
            self.fields['due_date'].initial = timezone.now().date() + timezone.timedelta(days=30)
            
        # Auto-populate billing info from customer if creating new invoice
        if not self.instance.pk and 'customer' in self.data:
            try:
                from accounts.models import User
                customer = User.objects.get(pk=self.data['customer'])
                self.fields['billing_name'].initial = f"{customer.first_name} {customer.last_name}".strip()
                self.fields['billing_email'].initial = customer.email
                if hasattr(customer, 'phone'):
                    self.fields['billing_phone'].initial = customer.phone
            except (User.DoesNotExist, KeyError):
                pass


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'payment_method', 'payment_status', 'payment_date', 
                 'amount', 'transaction_reference', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction ID or reference'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment notes...'
            }),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'expense_date', 'expense_type', 
                 'vendor_name', 'vendor_email', 'vendor_phone', 'notes']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expense description',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'required': True
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'expense_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'vendor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vendor/supplier name'
            }),
            'vendor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'vendor@example.com'
            }),
            'vendor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+974 XXXX XXXX'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default expense date to today for new expenses
        if not self.instance.pk:
            self.fields['expense_date'].initial = timezone.now().date()