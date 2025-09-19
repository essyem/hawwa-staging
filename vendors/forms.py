from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div, HTML
from crispy_forms.bootstrap import FormActions

from .models import VendorProfile, VendorDocument, VendorAvailability, VendorBlackoutDate


class VendorProfileForm(forms.ModelForm):
    """Form for updating vendor profile information"""
    
    class Meta:
        model = VendorProfile
        fields = [
            'business_name', 'business_type', 'business_license', 'tax_id',
            'business_phone', 'business_email', 'website', 'service_areas',
            'auto_accept_bookings', 'notification_email', 'notification_sms'
        ]
        widgets = {
            'service_areas': forms.Textarea(attrs={'rows': 3}),
            'business_phone': forms.TextInput(attrs={'placeholder': '+974XXXXXXXX'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h4 class="mb-3"><i class="fas fa-building"></i> Business Information</h4>'),
            Row(
                Column('business_name', css_class='form-group col-md-8 mb-3'),
                Column('business_type', css_class='form-group col-md-4 mb-3'),
            ),
            Row(
                Column('business_license', css_class='form-group col-md-6 mb-3'),
                Column('tax_id', css_class='form-group col-md-6 mb-3'),
            ),
            
            HTML('<h4 class="mb-3 mt-4"><i class="fas fa-address-book"></i> Contact Information</h4>'),
            Row(
                Column('business_phone', css_class='form-group col-md-6 mb-3'),
                Column('business_email', css_class='form-group col-md-6 mb-3'),
            ),
            'website',
            'service_areas',
            
            HTML('<h4 class="mb-3 mt-4"><i class="fas fa-cog"></i> Settings</h4>'),
            Row(
                Column('auto_accept_bookings', css_class='form-group col-md-4 mb-3'),
                Column('notification_email', css_class='form-group col-md-4 mb-3'),
                Column('notification_sms', css_class='form-group col-md-4 mb-3'),
            ),
            
            FormActions(
                Submit('submit', _('Update Profile'), css_class='btn btn-primary')
            )
        )


class VendorDocumentForm(forms.ModelForm):
    """Form for uploading vendor documents"""
    
    class Meta:
        model = VendorDocument
        fields = ['document_type', 'title', 'document_file', 'description', 'expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-3'),
                Column('title', css_class='form-group col-md-6 mb-3'),
            ),
            'document_file',
            'description',
            'expiry_date',
            FormActions(
                Submit('submit', _('Upload Document'), css_class='btn btn-primary')
            )
        )


class VendorAvailabilityForm(forms.ModelForm):
    """Form for setting vendor availability"""
    
    class Meta:
        model = VendorAvailability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('day_of_week', css_class='form-group col-md-4 mb-3'),
                Column('start_time', css_class='form-group col-md-3 mb-3'),
                Column('end_time', css_class='form-group col-md-3 mb-3'),
                Column('is_available', css_class='form-group col-md-2 mb-3'),
            ),
            FormActions(
                Submit('submit', _('Save Availability'), css_class='btn btn-primary')
            )
        )


class VendorBlackoutDateForm(forms.ModelForm):
    """Form for adding blackout dates"""
    
    class Meta:
        model = VendorBlackoutDate
        fields = ['start_date', 'end_date', 'reason', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-3'),
                Column('end_date', css_class='form-group col-md-6 mb-3'),
            ),
            'reason',
            'description',
            FormActions(
                Submit('submit', _('Add Blackout Period'), css_class='btn btn-warning')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError(_('End date must be after start date.'))
        
        return cleaned_data


class VendorServiceForm(forms.Form):
    """Form for quick service status updates"""
    
    AVAILABILITY_CHOICES = (
        ('available', _('Available')),
        ('unavailable', _('Unavailable')),
        ('limited', _('Limited Availability')),
    )
    
    service_id = forms.IntegerField(widget=forms.HiddenInput())
    status = forms.ChoiceField(choices=AVAILABILITY_CHOICES)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap4/layout/inline_field.html'
        self.helper.layout = Layout(
            'service_id',
            'status',
            Submit('submit', _('Update'), css_class='btn btn-sm btn-primary ml-2')
        )


class BulkBookingActionForm(forms.Form):
    """Form for bulk actions on bookings"""
    
    ACTION_CHOICES = (
        ('accept', _('Accept Selected')),
        ('reject', _('Reject Selected')),
        ('complete', _('Mark as Completed')),
        ('export', _('Export to CSV')),
    )
    
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    booking_ids = forms.CharField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            'booking_ids',
            'action',
            Submit('submit', _('Apply Action'), css_class='btn btn-primary ml-2')
        )