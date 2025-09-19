"""
URL configuration for Analytics app
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main analytics dashboard (admin/staff only)
    path('', views.analytics_dashboard, name='dashboard'),
    
    # Vendor-specific analytics
    path('vendor/<int:vendor_id>/', views.vendor_analytics_detail, name='vendor_detail'),
    
    # Quality rankings
    path('rankings/', views.quality_rankings, name='rankings'),
    
    # Performance trends
    path('trends/', views.performance_trends, name='trends'),
    
    # Vendor dashboard (for individual vendors)
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    
    # Smart Vendor Assignment views
    path('assignments/', views.assignment_dashboard, name='assignment_dashboard'),
    path('assignments/vendor/<int:vendor_id>/', views.vendor_assignment_detail, name='vendor_assignment_detail'),
    path('assignments/analytics/', views.assignment_analytics, name='assignment_analytics'),
    path('assignments/logs/', views.assignment_logs, name='assignment_logs'),
    
    # API endpoints for AJAX chart updates
    path('api/platform-stats/', views.api_platform_stats, name='api_platform_stats'),
    path('api/vendor-performance/<int:vendor_id>/', views.api_vendor_performance_chart, name='api_vendor_performance'),
    path('api/quality-trends/', views.api_quality_trends, name='api_quality_trends'),
    
    # Smart Assignment API endpoints
    path('api/assignment-stats/', views.api_assignment_stats, name='api_assignment_stats'),
    path('api/vendor-availability/<int:vendor_id>/', views.api_vendor_availability, name='api_vendor_availability'),
    path('api/assignment-trends/', views.api_assignment_trends, name='api_assignment_trends'),
    path('api/auto-assign/', views.auto_assign_pending_bookings, name='auto_assign_pending_bookings'),
]