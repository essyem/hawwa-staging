from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets and UI views
from .views import (
	ChangeRequestViewSet,
	IncidentViewSet,
	LeadViewSet,
	CommentViewSet,
	ActivityViewSet,
	RoleViewSet,
	RoleAssignmentViewSet,
	cr_detail_view,
    dashboard_view,
    ChangeRequestListView,
    IncidentListView,
    LeadListView,
    RoleListView,
    ActivityListView,
)

router = DefaultRouter()
router.register(r'change-requests', ChangeRequestViewSet, basename='change-request')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'role-assignments', RoleAssignmentViewSet, basename='role-assignment')
router.register(r'activity', ActivityViewSet, basename='activity')

app_name = 'change_management'

# API URLs
api_urlpatterns = router.urls

# Frontend UI URLs  
urlpatterns = [
    # Dashboard
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', dashboard_view, name='change_dashboard'),
    
    # Change Requests
    path('change-requests/', ChangeRequestListView.as_view(), name='change_list'),
    path('change-request/<int:pk>/', cr_detail_view, name='cr_detail'),
    
    # Incidents  
    path('incidents/', IncidentListView.as_view(), name='incident_list'),
    
    # Leads
    path('leads/', LeadListView.as_view(), name='lead_list'),
    
    # Roles
    path('roles/', RoleListView.as_view(), name='role_list'),
    
    # Activities
    path('activities/', ActivityListView.as_view(), name='activity_list'),
]

# Add API URLs with 'api/' prefix
urlpatterns += [path('api/', include(api_urlpatterns))]
