from django.urls import path
from .views import (
    HomePageView,
    AboutPageView,
    ContactPageView,
    TermsPageView,
    PrivacyPageView,
    FAQPageView
)

app_name = 'core'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('about/', AboutPageView.as_view(), name='about'),
    path('contact/', ContactPageView.as_view(), name='contact'),
    path('terms/', TermsPageView.as_view(), name='terms'),
    path('privacy/', PrivacyPageView.as_view(), name='privacy'),
    path('faq/', FAQPageView.as_view(), name='faq'),
]