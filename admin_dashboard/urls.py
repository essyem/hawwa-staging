from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    
    # User management
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/update-status/', views.update_user_status, name='update_user_status'),
    
    # Booking management
    path('bookings/', views.BookingManagementView.as_view(), name='booking_management'),
    
    # Vendor management
    path('vendors/', views.VendorManagementView.as_view(), name='vendor_management'),
    path('vendors/update-status/', views.update_vendor_status, name='update_vendor_status'),
    
    # Analytics API
    path('api/analytics/', views.admin_analytics_api, name='analytics_api'),
]