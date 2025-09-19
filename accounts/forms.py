from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import User
from .profile_models import (
    MotherProfile, AccommodationProviderProfile, CaretakerProviderProfile,
    WellnessProviderProfile, MeditationConsultantProfile, MentalHealthConsultantProfile,
    FoodProviderProfile
)

class UserRegistrationForm(UserCreationForm):
    """Base form for user registration."""
    agree_terms = forms.BooleanField(
        label=_('I agree to the Terms and Conditions'),
        required=True,
        error_messages={
            'required': _('You must agree to the terms and conditions to register')
        }
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'user_type',
                  'password1', 'password2', 'agree_terms')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['agree_terms'].widget.attrs.update({'class': 'form-check-input'})

class LoginForm(AuthenticationForm):
    """Custom login form."""
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter your email')})
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Enter your password')})
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }
    
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive',
                )
        return self.cleaned_data

# Specific registration forms for each user type
class MotherRegistrationForm(UserRegistrationForm):
    """Registration form for mothers."""
    due_date = forms.DateField(
        label=_('Due Date'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'MOTHER'
        
        if commit:
            user.save()
            # Create the mother profile
            mother_profile = MotherProfile(
                user=user,
                due_date=self.cleaned_data.get('due_date'),
            )
            mother_profile.save()
            
        return user

class AccommodationProviderRegistrationForm(UserRegistrationForm):
    """Registration form for accommodation providers."""
    business_name = forms.CharField(
        max_length=200,
        label=_('Business Name'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    property_type = forms.CharField(
        max_length=100,
        label=_('Property Type'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'ACCOMMODATION'
        
        if commit:
            user.save()
            # Create the accommodation provider profile
            accommodation_profile = AccommodationProviderProfile(
                user=user,
                business_name=self.cleaned_data.get('business_name'),
                property_type=self.cleaned_data.get('property_type'),
            )
            accommodation_profile.save()
            
        return user

class CaretakerProviderRegistrationForm(UserRegistrationForm):
    """Registration form for caretaker providers."""
    years_of_experience = forms.IntegerField(
        label=_('Years of Experience'),
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    specializations = forms.CharField(
        label=_('Specializations'),
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'CARETAKER'
        
        if commit:
            user.save()
            # Create the caretaker provider profile
            caretaker_profile = CaretakerProviderProfile(
                user=user,
                years_of_experience=self.cleaned_data.get('years_of_experience'),
                specializations=self.cleaned_data.get('specializations'),
            )
            caretaker_profile.save()
            
        return user

class WellnessProviderRegistrationForm(UserRegistrationForm):
    """Registration form for wellness service providers."""
    service_type = forms.CharField(
        max_length=100,
        label=_('Service Type'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    years_of_experience = forms.IntegerField(
        label=_('Years of Experience'),
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'WELLNESS'
        
        if commit:
            user.save()
            # Create the wellness provider profile
            wellness_profile = WellnessProviderProfile(
                user=user,
                service_type=self.cleaned_data.get('service_type'),
                years_of_experience=self.cleaned_data.get('years_of_experience'),
            )
            wellness_profile.save()
            
        return user

class MeditationConsultantRegistrationForm(UserRegistrationForm):
    """Registration form for meditation consultants."""
    practice_type = forms.CharField(
        max_length=100,
        label=_('Practice Type'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    years_of_experience = forms.IntegerField(
        label=_('Years of Experience'),
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'MEDITATION'
        
        if commit:
            user.save()
            # Create the meditation consultant profile
            meditation_profile = MeditationConsultantProfile(
                user=user,
                practice_type=self.cleaned_data.get('practice_type'),
                years_of_experience=self.cleaned_data.get('years_of_experience'),
            )
            meditation_profile.save()
            
        return user

class MentalHealthConsultantRegistrationForm(UserRegistrationForm):
    """Registration form for mental health consultants."""
    title = forms.CharField(
        max_length=100,
        label=_('Professional Title'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    years_of_experience = forms.IntegerField(
        label=_('Years of Experience'),
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'MENTAL_HEALTH'
        
        if commit:
            user.save()
            # Create the mental health consultant profile
            mental_health_profile = MentalHealthConsultantProfile(
                user=user,
                title=self.cleaned_data.get('title'),
                years_of_experience=self.cleaned_data.get('years_of_experience'),
            )
            mental_health_profile.save()
            
        return user

class FoodProviderRegistrationForm(UserRegistrationForm):
    """Registration form for food providers."""
    business_name = forms.CharField(
        max_length=200,
        label=_('Business Name'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cuisine_types = forms.CharField(
        label=_('Cuisine Types'),
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        model = User
        fields = UserRegistrationForm.Meta.fields
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'FOOD'
        
        if commit:
            user.save()
            # Create the food provider profile
            food_profile = FoodProviderProfile(
                user=user,
                business_name=self.cleaned_data.get('business_name'),
                cuisine_types=self.cleaned_data.get('cuisine_types'),
            )
            food_profile.save()
            
        return user