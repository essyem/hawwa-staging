from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Booking, BookingItem, BookingPayment

class BookingForm(forms.ModelForm):
    """
    Form for creating and updating bookings
    """
    class Meta:
        model = Booking
        fields = [
            'service', 'start_date', 'end_date', 'start_time', 'end_time',
            'address', 'city', 'postal_code', 'client_phone', 'client_email',
            'emergency_contact', 'emergency_phone', 'special_instructions', 
            'notes', 'priority'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'special_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+974 7212 6440'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+974 7212 6440'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].widget.attrs.update({'class': 'form-select'})
        
        # Set some fields as not required for flexibility
        optional_fields = ['notes', 'special_instructions', 'end_time', 'city', 'postal_code', 
                          'emergency_contact', 'emergency_phone']
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
        
        # Auto-populate user email if available
        if hasattr(self, 'user') and self.user.email and not self.instance.pk:
            self.fields['client_email'].initial = self.user.email
            
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validate dates
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                _("End date cannot be earlier than start date.")
            )
            
        # Validate that booking is not in the past
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError(
                _("Booking date cannot be in the past.")
            )
            
        # Validate times if both are provided
        if start_time and end_time and start_date == end_date:
            if start_time >= end_time:
                raise forms.ValidationError(
                    _("End time must be after start time on the same day.")
                )
        
        return cleaned_data


class QuickBookingForm(forms.ModelForm):
    """
    Simplified form for quick bookings
    """
    class Meta:
        model = Booking
        fields = ['service', 'start_date', 'start_time', 'address', 'client_phone']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+974 7212 6440'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].widget.attrs.update({'class': 'form-select'})


class BookingItemForm(forms.ModelForm):
    """
    Form for creating and updating booking items
    """
    class Meta:
        model = BookingItem
        fields = ['name', 'description', 'quantity', 'price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class BookingStatusForm(forms.ModelForm):
    """
    Form for updating booking status (admin use)
    """
    class Meta:
        model = Booking
        fields = ['status', 'internal_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'internal_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class BookingPaymentForm(forms.ModelForm):
    """
    Form for recording booking payments
    """
    class Meta:
        model = BookingPayment
        fields = ['amount', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_id'].required = False
        self.fields['notes'].required = False


class BookingSearchForm(forms.Form):
    """
    Form for searching and filtering bookings
    """
    STATUS_CHOICES = [('', _('All Status'))] + list(Booking.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', _('All Priorities'))] + list(Booking.PRIORITY_CHOICES)
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by booking number, client name, or service...')
        })
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )