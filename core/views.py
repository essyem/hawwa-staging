from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

class HomePageView(TemplateView):
    """View for the home page."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any context data needed for the home page
        return context

class AboutPageView(TemplateView):
    """View for the about page."""
    template_name = 'core/about.html'

class ContactPageView(TemplateView):
    """View for the contact page."""
    template_name = 'core/contact.html'
    
class TermsPageView(TemplateView):
    """View for the terms and conditions page."""
    template_name = 'core/terms.html'

class PrivacyPageView(TemplateView):
    """View for the privacy policy page."""
    template_name = 'core/privacy.html'

class FAQPageView(TemplateView):
    """View for the FAQ page."""
    template_name = 'core/faq.html'

@method_decorator(login_required, name='dispatch')
class AdminPortalShowcaseView(LoginRequiredMixin, TemplateView):
    """Showcase view for the new IFMS-style admin portal."""
    template_name = 'admin_portal_showcase.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add some demo data for the showcase
        context.update({
            'total_users': 1247,
            'active_bookings': 89,
            'total_services': 34,
            'active_vendors': 17,
        })
        
        return context
