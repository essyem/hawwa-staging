"""
URL configuration for hawwa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from core import views as core_views
from accounts import views as accounts_views
from accounts.admin_extensions import hawwa_admin_site

# Custom admin site configuration
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    path('hawwa-admin/', hawwa_admin_site.urls),  # Enhanced admin
    
    # Global auth URLs (for convenience)
    path('login/', accounts_views.LoginView.as_view(), name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('register/', accounts_views.RegisterView.as_view(), name='register'),
    
    # Core URLs
    path('', include('core.urls', namespace='core')),
    
    # App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('services/', include('services.urls', namespace='services')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('vendors/', include('vendors.urls', namespace='vendors')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('wellness/', include('wellness.urls', namespace='wellness')),
    path('ai-buddy/', include('ai_buddy.urls', namespace='ai_buddy')),
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),
    path('reporting/', include('reporting.urls', namespace='reporting')),
    
    # API URLs
    path('api/v1/', include('api.urls')),
    path('api/', include('core.api_urls')),
    
    # i18n URLs for language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
