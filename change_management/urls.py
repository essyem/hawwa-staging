from rest_framework.routers import DefaultRouter
from .views import ChangeRequestViewSet, IncidentViewSet, LeadViewSet

router = DefaultRouter()
router.register(r'change-requests', ChangeRequestViewSet, basename='change-request')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'leads', LeadViewSet, basename='lead')

urlpatterns = router.urls
