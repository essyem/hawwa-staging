from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from .models import (
    Company, Department, Position, Grade, EmployeeProfile,
    LeaveType, LeaveBalance, LeaveApplication, 
    TrainingCategory, TrainingProgram, TrainingSession, TrainingEnrollment,
    PerformanceCycle, PerformanceReview,
    PayrollPeriod, PayrollItem
)
from .serializers import (
    CompanySerializer, DepartmentSerializer, PositionSerializer, GradeSerializer,
    EmployeeProfileListSerializer, EmployeeProfileDetailSerializer,
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveApplicationSerializer,
    TrainingCategorySerializer, TrainingProgramSerializer, TrainingSessionSerializer, TrainingEnrollmentSerializer,
    PerformanceCycleSerializer, PerformanceReviewSerializer,
    PayrollPeriodSerializer, PayrollItemSerializer,
    DashboardStatsSerializer, RecentActivitySerializer
)


# ============================================================================
# ORGANIZATIONAL API VIEWSETS
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'company']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        department = self.get_object()
        employees = EmployeeProfile.objects.filter(department=department)
        serializer = EmployeeProfileListSerializer(employees, many=True)
        return Response(serializer.data)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['department', 'level', 'is_active']
    search_fields = ['title', 'code']
    ordering_fields = ['title', 'level']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['level', 'name']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


# ============================================================================
# EMPLOYEE API VIEWSETS
# ============================================================================

class EmployeeProfileViewSet(viewsets.ModelViewSet):
    queryset = EmployeeProfile.objects.select_related('user', 'department', 'position', 'grade')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['department', 'position', 'status', 'employment_type']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'user__email']
    ordering_fields = ['user__first_name', 'hire_date', 'employee_id']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeProfileListSerializer
        return EmployeeProfileDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own profile
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def leave_balances(self, request, pk=None):
        employee = self.get_object()
        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=timezone.now().year
        ).select_related('leave_type')
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def training_enrollments(self, request, pk=None):
        employee = self.get_object()
        enrollments = TrainingEnrollment.objects.filter(
            employee=employee
        ).select_related('session__program')
        serializer = TrainingEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payroll_history(self, request, pk=None):
        employee = self.get_object()
        payrolls = PayrollItem.objects.filter(
            employee=employee
        ).select_related('payroll_period').order_by('-payroll_period__end_date')
        serializer = PayrollItemSerializer(payrolls, many=True)
        return Response(serializer.data)


# ============================================================================
# LEAVE MANAGEMENT API VIEWSETS
# ============================================================================

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'is_paid']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveBalance.objects.select_related('employee__user', 'leave_type')
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['year', 'leave_type', 'employee__department']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own leave balances
        if not self.request.user.is_staff:
            try:
                employee = EmployeeProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    queryset = LeaveApplication.objects.select_related('employee__user', 'leave_type', 'approved_by')
    serializer_class = LeaveApplicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'leave_type', 'start_date']
    ordering_fields = ['applied_date', 'start_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own leave applications
        if not self.request.user.is_staff:
            try:
                employee = EmployeeProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def perform_create(self, serializer):
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            serializer.save(employee=employee, applied_date=timezone.now().date())
        except EmployeeProfile.DoesNotExist:
            raise serializers.ValidationError("Employee profile not found.")
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        leave_application = self.get_object()
        leave_application.status = 'approved'
        leave_application.approved_by = request.user
        leave_application.approved_date = timezone.now().date()
        leave_application.save()
        
        serializer = self.get_serializer(leave_application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        leave_application = self.get_object()
        leave_application.status = 'rejected'
        leave_application.approved_by = request.user
        leave_application.approved_date = timezone.now().date()
        leave_application.save()
        
        serializer = self.get_serializer(leave_application)
        return Response(serializer.data)


# ============================================================================
# TRAINING API VIEWSETS
# ============================================================================

class TrainingCategoryViewSet(viewsets.ModelViewSet):
    queryset = TrainingCategory.objects.all()
    serializer_class = TrainingCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class TrainingProgramViewSet(viewsets.ModelViewSet):
    queryset = TrainingProgram.objects.select_related('category', 'instructor__user')
    serializer_class = TrainingProgramSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'level', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'start_date']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        program = self.get_object()
        try:
            employee = EmployeeProfile.objects.get(user=request.user)
            enrollment, created = TrainingEnrollment.objects.get_or_create(
                employee=employee,
                program=program,
                defaults={
                    'enrollment_date': timezone.now().date(),
                    'status': 'enrolled'
                }
            )
            
            if created:
                return Response({'message': 'Successfully enrolled in the program'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Already enrolled in this program'}, status=status.HTTP_200_OK)
                
        except EmployeeProfile.DoesNotExist:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)


class TrainingEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = TrainingEnrollment.objects.select_related('employee__user', 'session__program')
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'session__program__category']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own enrollments
        if not self.request.user.is_staff:
            try:
                employee = EmployeeProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


# ============================================================================
# PERFORMANCE API VIEWSETS
# ============================================================================

class PerformanceReviewViewSet(viewsets.ModelViewSet):
    queryset = PerformanceReview.objects.select_related('employee__user', 'reviewer', 'cycle')
    serializer_class = PerformanceReviewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'overall_rating', 'cycle']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own reviews
        if not self.request.user.is_staff:
            try:
                employee = EmployeeProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


# ============================================================================
# PAYROLL API VIEWSETS
# ============================================================================

class PayrollItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PayrollItem.objects.select_related('employee__user', 'payroll_period')
    serializer_class = PayrollItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'payroll_period']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-admin users can only see their own payroll items
        if not self.request.user.is_staff:
            try:
                employee = EmployeeProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset


# ============================================================================
# DASHBOARD & ANALYTICS API VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    
    # Basic counts
    total_employees = EmployeeProfile.objects.filter(status='active').count()
    active_employees = EmployeeProfile.objects.filter(status='active').count()
    total_departments = Department.objects.filter(is_active=True).count()
    pending_leaves = LeaveApplication.objects.filter(status='pending').count()
    active_training_programs = TrainingProgram.objects.filter(is_active=True).count()
    
    # This month hires
    this_month_start = timezone.now().replace(day=1)
    this_month_hires = EmployeeProfile.objects.filter(
        hire_date__gte=this_month_start
    ).count()
    
    # Average salary
    avg_salary = EmployeeProfile.objects.filter(
        status='active'
    ).aggregate(
        avg_basic=Avg('basic_salary'),
        avg_housing=Avg('housing_allowance'),
        avg_transport=Avg('transport_allowance'),
        avg_other=Avg('other_allowances')
    )
    
    average_salary = (
        (avg_salary['avg_basic'] or 0) +
        (avg_salary['avg_housing'] or 0) +
        (avg_salary['avg_transport'] or 0) +
        (avg_salary['avg_other'] or 0)
    )
    
    stats = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_departments': total_departments,
        'pending_leaves': pending_leaves,
        'active_training_programs': active_training_programs,
        'this_month_hires': this_month_hires,
        'average_salary': round(average_salary, 2)
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_analytics(request):
    """Get department-wise analytics"""
    
    departments = Department.objects.filter(is_active=True).annotate(
        employee_count=Count('employees'),
        avg_salary=Avg('employees__basic_salary')
    ).values('name', 'employee_count', 'avg_salary')
    
    return Response(list(departments))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leave_analytics(request):
    """Get leave analytics"""
    
    # Leave applications by month
    monthly_leaves = LeaveApplication.objects.filter(
        applied_date__year=timezone.now().year
    ).extra(
        select={'month': 'EXTRACT(month FROM applied_date)'}
    ).values('month').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected')),
        pending=Count('id', filter=Q(status='pending'))
    ).order_by('month')
    
    # Leave types usage
    leave_types = LeaveApplication.objects.values(
        'leave_type__name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    return Response({
        'monthly_leaves': list(monthly_leaves),
        'leave_types': list(leave_types)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_analytics(request):
    """Get training analytics"""
    
    # Training completion rates by category
    categories = TrainingCategory.objects.annotate(
        total_programs=Count('programs'),
        total_enrollments=Count('programs__enrollments'),
        completed_enrollments=Count('programs__enrollments', filter=Q(programs__enrollments__status='completed'))
    ).values('name', 'total_programs', 'total_enrollments', 'completed_enrollments')
    
    # Monthly training enrollments
    monthly_enrollments = TrainingEnrollment.objects.filter(
        enrollment_date__year=timezone.now().year
    ).extra(
        select={'month': 'EXTRACT(month FROM enrollment_date)'}
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')
    
    return Response({
        'categories': list(categories),
        'monthly_enrollments': list(monthly_enrollments)
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def payroll_analytics(request):
    """Get payroll analytics"""
    
    # Monthly payroll totals
    monthly_payroll = PayrollItem.objects.filter(
        payroll_period__start_date__year=timezone.now().year
    ).values(
        'payroll_period__name'
    ).annotate(
        total_gross=Sum('gross_salary'),
        total_deductions=Sum('total_deductions'),
        total_net=Sum('net_salary'),
        employee_count=Count('employee', distinct=True)
    ).order_by('payroll_period__start_date')
    
    # Department-wise payroll
    dept_payroll = PayrollItem.objects.values(
        'employee__department__name'
    ).annotate(
        total_payroll=Sum('net_salary'),
        employee_count=Count('employee', distinct=True),
        avg_salary=Avg('net_salary')
    ).order_by('-total_payroll')
    
    return Response({
        'monthly_payroll': list(monthly_payroll),
        'department_payroll': list(dept_payroll)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activities(request):
    """Get recent activities across the system"""
    activities = []
    
    # Recent employee additions
    recent_employees = EmployeeProfile.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).select_related('user')[:5]
    
    for emp in recent_employees:
        activities.append({
            'type': 'employee',
            'title': 'New Employee Added',
            'description': f'{emp.user.get_full_name()} joined {emp.department.name}',
            'timestamp': emp.created_at,
            'user': emp.user.get_full_name()
        })
    
    # Recent leave applications
    recent_leaves = LeaveApplication.objects.filter(
        applied_date__gte=timezone.now().date() - timedelta(days=7)
    ).select_related('employee__user')[:5]
    
    for leave in recent_leaves:
        activities.append({
            'type': 'leave',
            'title': 'Leave Application',
            'description': f'{leave.employee.user.get_full_name()} applied for {leave.leave_type.name}',
            'timestamp': timezone.datetime.combine(leave.applied_date, timezone.datetime.min.time()),
            'user': leave.employee.user.get_full_name()
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return Response(activities[:10])


# ============================================================================
# UTILITY API VIEWS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_employees(request):
    """Search employees by name or employee ID"""
    query = request.GET.get('q', '')
    
    if query:
        employees = EmployeeProfile.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query)
        ).select_related('user', 'department', 'position')[:10]
        
        serializer = EmployeeProfileListSerializer(employees, many=True)
        return Response(serializer.data)
    
    return Response([])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_suggestions(request):
    """Get employee suggestions for autocomplete"""
    query = request.GET.get('q', '')
    
    if query:
        employees = EmployeeProfile.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query)
        ).select_related('user')[:5]
        
        suggestions = [
            {
                'id': emp.id,
                'name': emp.user.get_full_name(),
                'employee_id': emp.employee_id,
                'department': emp.department.name if emp.department else ''
            }
            for emp in employees
        ]
        
        return Response(suggestions)
    
    return Response([])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_status_api(request):
    """Get status of scheduled reports for real-time updates"""
    try:
        # For now, return a basic structure for scheduled reports
        # This can be expanded when we have actual scheduled report models
        scheduled_reports = [
            {
                'id': 1,
                'name': 'Employee Report',
                'is_active': True,
                'last_run': timezone.now().isoformat(),
                'status': 'completed'
            },
            {
                'id': 2,
                'name': 'Payroll Report',
                'is_active': True,
                'last_run': timezone.now().isoformat(),
                'status': 'running'
            },
            {
                'id': 3,
                'name': 'Attendance Report',
                'is_active': False,
                'last_run': None,
                'status': 'stopped'
            }
        ]
        
        return Response({
            'scheduled_reports': scheduled_reports,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch report status', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
