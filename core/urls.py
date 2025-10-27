from django.urls import path, include
from .views import (
    HomePageView,
    AboutPageView,
    ContactPageView,
    TermsPageView,
    PrivacyPageView,
    FAQPageView,
    AdminPortalShowcaseView
)

# Import admin views
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from admin_views import (
    admin_dashboard,
    AdminServiceListView,
    AdminServiceDetailView,
    AdminServiceCreateView,
    AdminServiceUpdateView,
    AdminBookingListView,
    admin_dashboard_refresh,
    export_services,
    export_bookings,
)

app_name = 'core'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('about/', AboutPageView.as_view(), name='about'),
    path('contact/', ContactPageView.as_view(), name='contact'),
    path('terms/', TermsPageView.as_view(), name='terms'),
    path('privacy/', PrivacyPageView.as_view(), name='privacy'),
    path('faq/', FAQPageView.as_view(), name='faq'),
    path('admin-portal/', AdminPortalShowcaseView.as_view(), name='admin_portal_showcase'),
    
    # Admin Dashboard
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/refresh/', admin_dashboard_refresh, name='admin_dashboard_refresh'),
    
    # Admin Services
    path('admin/services/', AdminServiceListView.as_view(), name='admin_service_list'),
    path('admin/services/create/', AdminServiceCreateView.as_view(), name='admin_service_create'),
    path('admin/services/<int:pk>/', AdminServiceDetailView.as_view(), name='admin_service_detail'),
    path('admin/services/<int:pk>/edit/', AdminServiceUpdateView.as_view(), name='admin_service_edit'),
    path('admin/services/export/', export_services, name='export_services'),
    
    # Admin Bookings  
    path('admin/bookings/', AdminBookingListView.as_view(), name='admin_booking_list'),
    path('admin/bookings/create/', AdminPortalShowcaseView.as_view(), name='admin_booking_create'),  # Placeholder
    path('admin/bookings/export/', export_bookings, name='export_bookings'),
]