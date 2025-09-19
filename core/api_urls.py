from django.urls import path, include
from rest_framework import routers

# API router
router = routers.DefaultRouter()

urlpatterns = [
    # Include the router generated URLs
    path('', include(router.urls)),
    
    # API authentication
    path('auth/', include('rest_framework.urls')),
]