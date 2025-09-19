from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ServiceReview, Service

class ServiceSearchForm(forms.Form):
    """Form for searching services."""
    query = forms.CharField(
        label=_("Search"), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Search services...')})
    )
    
    category = forms.ChoiceField(
        label=_("Category"),
        required=False,
        choices=[('', _('All Categories'))],  # Will be populated dynamically
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_price = forms.DecimalField(
        label=_("Min Price"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': _('Min')})
    )
    
    max_price = forms.DecimalField(
        label=_("Max Price"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': _('Max')})
    )
    
    sort_by = forms.ChoiceField(
        label=_("Sort By"),
        required=False,
        choices=[
            ('', _('Default')),
            ('price_low', _('Price: Low to High')),
            ('price_high', _('Price: High to Low')),
            ('newest', _('Newest First')),
            ('name', _('Name A-Z')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        categories = kwargs.pop('categories', [])
        super().__init__(*args, **kwargs)
        
        # Update category choices with available categories
        if categories:
            category_choices = [('', _('All Categories'))]
            category_choices.extend([(c.id, c.name) for c in categories])
            self.fields['category'].choices = category_choices


class ServiceReviewForm(forms.ModelForm):
    """Form for adding service reviews."""
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Write your review here...')
            }),
        }
        

class ServiceInquiryForm(forms.Form):
    """Form for service inquiries."""
    name = forms.CharField(
        label=_("Full Name"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    phone = forms.CharField(
        label=_("Phone Number"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    service = forms.ModelChoiceField(
        label=_("Service"),
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    preferred_date = forms.DateField(
        label=_("Preferred Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    def __init__(self, *args, **kwargs):
        service_id = kwargs.pop('service_id', None)
        super().__init__(*args, **kwargs)
        
        # If a service_id is provided, set it as the initial value
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
                self.fields['service'].initial = service
                # Make the field readonly if a specific service is pre-selected
                self.fields['service'].widget.attrs['disabled'] = 'disabled'
            except Service.DoesNotExist:
                pass