from django.urls import path
from rest_framework.routers import DefaultRouter

# Import viewsets and UI view
from .views import (
	ChangeRequestViewSet,
	IncidentViewSet,
	LeadViewSet,
	CommentViewSet,
	ActivityViewSet,
	RoleViewSet,
	RoleAssignmentViewSet,
	cr_detail_view,
)

router = DefaultRouter()
router.register(r'change-requests', ChangeRequestViewSet, basename='change-request')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'role-assignments', RoleAssignmentViewSet, basename='role-assignment')
router.register(r'activity', ActivityViewSet, basename='activity')

urlpatterns = router.urls

urlpatterns += [
	path('ui/change-request/<int:pk>/', cr_detail_view, name='cr_detail'),
]
