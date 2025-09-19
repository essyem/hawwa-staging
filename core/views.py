from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

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
