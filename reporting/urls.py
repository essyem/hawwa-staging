from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    # Dashboard views
    path('dashboard/', views.analytics_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/metrics/', views.metrics_api, name='metrics_api'),
    path('api/insights/', views.insights_api, name='insights_api'),
    path('api/generate-report/', views.generate_report_api, name='generate_report_api'),
]