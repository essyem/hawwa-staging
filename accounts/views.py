from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from .forms import (
    LoginForm, UserRegistrationForm, MotherRegistrationForm, AccommodationProviderRegistrationForm,
    CaretakerProviderRegistrationForm, WellnessProviderRegistrationForm,
    MeditationConsultantRegistrationForm, MentalHealthConsultantRegistrationForm,
    FoodProviderRegistrationForm
)
from .models import User
from .profile_models import (
    MotherProfile, AccommodationProviderProfile, CaretakerProviderProfile,
    WellnessProviderProfile, MeditationConsultantProfile, MentalHealthConsultantProfile,
    FoodProviderProfile
)

class RegisterView(TemplateView):
    """View to choose which type of user to register as."""
    template_name = 'accounts/register_choice.html'

class MotherRegistrationView(CreateView):
    """View for mother registration."""
    template_name = 'accounts/register.html'
    form_class = MotherRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Mother')
        context['user_type'] = 'mother'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class AccommodationProviderRegistrationView(CreateView):
    """View for accommodation provider registration."""
    template_name = 'accounts/register.html'
    form_class = AccommodationProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as an Accommodation Provider')
        context['user_type'] = 'accommodation'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class CaretakerProviderRegistrationView(CreateView):
    """View for caretaker provider registration."""
    template_name = 'accounts/register.html'
    form_class = CaretakerProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Caretaker Provider')
        context['user_type'] = 'caretaker'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class WellnessProviderRegistrationView(CreateView):
    """View for wellness provider registration."""
    template_name = 'accounts/register.html'
    form_class = WellnessProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Wellness Service Provider')
        context['user_type'] = 'wellness'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class MeditationConsultantRegistrationView(CreateView):
    """View for meditation consultant registration."""
    template_name = 'accounts/register.html'
    form_class = MeditationConsultantRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Meditation Consultant')
        context['user_type'] = 'meditation'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class MentalHealthConsultantRegistrationView(CreateView):
    """View for mental health consultant registration."""
    template_name = 'accounts/register.html'
    form_class = MentalHealthConsultantRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Mental Health Consultant')
        context['user_type'] = 'mental_health'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class FoodProviderRegistrationView(CreateView):
    """View for food provider registration."""
    template_name = 'accounts/register.html'
    form_class = FoodProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Food Provider')
        context['user_type'] = 'food'
        return context
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Your account has been successfully created!'))
        return super().form_valid(form)

class LoginView(FormView):
    """View for user login."""
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core:home')
    
    def form_valid(self, form):
        login(self.request, form.get_user())
        remember_me = form.cleaned_data.get('remember_me')
        
        if not remember_me:
            self.request.session.set_expiry(0)
        
        messages.success(self.request, _('You have successfully logged in.'))
        return super().form_valid(form)

@login_required
def logout_view(request):
    """View for user logout."""
    logout(request)
    messages.success(request, _('You have successfully logged out.'))
    return redirect('home')

@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """View for user profile."""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        
        # Get the appropriate profile based on user type
        if user.user_type == 'MOTHER':
            context['profile'] = MotherProfile.objects.get(user=user)
        elif user.user_type == 'ACCOMMODATION':
            context['profile'] = AccommodationProviderProfile.objects.get(user=user)
        elif user.user_type == 'CARETAKER':
            context['profile'] = CaretakerProviderProfile.objects.get(user=user)
        elif user.user_type == 'WELLNESS':
            context['profile'] = WellnessProviderProfile.objects.get(user=user)
        elif user.user_type == 'MEDITATION':
            context['profile'] = MeditationConsultantProfile.objects.get(user=user)
        elif user.user_type == 'MENTAL_HEALTH':
            context['profile'] = MentalHealthConsultantProfile.objects.get(user=user)
        elif user.user_type == 'FOOD':
            context['profile'] = FoodProviderProfile.objects.get(user=user)
            
        return context
