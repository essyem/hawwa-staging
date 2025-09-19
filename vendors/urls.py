from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Dashboard
    path('', views.vendor_dashboard, name='dashboard'),
    
    # Profile Management
    path('profile/', views.VendorProfileDetailView.as_view(), name='profile'),
    path('profile/edit/', views.VendorProfileUpdateView.as_view(), name='profile_edit'),
    
    # Booking Management
    path('bookings/', views.vendor_bookings, name='bookings'),
    path('bookings/<int:booking_id>/', views.vendor_booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    
    # Service Management
    path('services/', views.vendor_services, name='services'),
    
    # Analytics
    path('analytics/', views.vendor_analytics, name='analytics'),
    
    # Availability Management
    path('availability/', views.vendor_availability, name='availability'),
    
    # Document Management
    path('documents/', views.vendor_documents, name='documents'),
    
    # Payments
    path('payments/', views.vendor_payments, name='payments'),
]