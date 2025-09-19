from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    ServiceCategoryViewSet,
    ServiceViewSet,
    BookingViewSet,
    BookingItemViewSet
)
from .auth import CustomAuthToken
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Documentation schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Hawwa API",
        default_version='v1',
        description="API documentation for Hawwa Postpartum Care Platform",
        terms_of_service="https://www.hawwa.com/terms/",
        contact=openapi.Contact(email="hello@trendzapps.com"),
        license=openapi.License(name="Private License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', ServiceCategoryViewSet, basename='category')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'booking-items', BookingItemViewSet, basename='bookingitem')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls', namespace='api_rest_framework')),
    path('token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('auth/token/', CustomAuthToken.as_view(), name='token_obtain'),
    
    # Swagger documentation endpoints
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]