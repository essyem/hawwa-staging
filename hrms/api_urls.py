from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'api_v1'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'companies', api_views.CompanyViewSet)
router.register(r'departments', api_views.DepartmentViewSet)
router.register(r'positions', api_views.PositionViewSet)
router.register(r'grades', api_views.GradeViewSet)
router.register(r'employees', api_views.EmployeeProfileViewSet)
router.register(r'leave-types', api_views.LeaveTypeViewSet)
router.register(r'leave-balances', api_views.LeaveBalanceViewSet)
router.register(r'leave-applications', api_views.LeaveApplicationViewSet)
router.register(r'training-categories', api_views.TrainingCategoryViewSet)
router.register(r'training-programs', api_views.TrainingProgramViewSet)
router.register(r'training-enrollments', api_views.TrainingEnrollmentViewSet)
router.register(r'performance-reviews', api_views.PerformanceReviewViewSet)
router.register(r'payroll-items', api_views.PayrollItemViewSet)

# API URL patterns
urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Dashboard & Analytics
    path('dashboard/stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('analytics/departments/', api_views.department_analytics, name='department_analytics'),
    path('analytics/leaves/', api_views.leave_analytics, name='leave_analytics'),
    path('analytics/training/', api_views.training_analytics, name='training_analytics'),
    path('analytics/payroll/', api_views.payroll_analytics, name='payroll_analytics'),
    
    # Recent Activities
    path('activities/recent/', api_views.recent_activities, name='recent_activities'),
    
    # Reports
    path('reports/status/', api_views.report_status_api, name='report_status_api'),
    
    # Utility Endpoints
    path('search/employees/', api_views.search_employees, name='search_employees'),
    path('suggestions/employees/', api_views.employee_suggestions, name='employee_suggestions'),
]
