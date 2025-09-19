from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views.generic import (TemplateView, ListView, CreateView, 
    UpdateView, DetailView, DeleteView, View)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg, Min, Max, F
from django.utils import timezone
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
import math

from .models import (
    Company, Department, Position, Grade, EmployeeProfile,
    LeaveType, LeaveBalance, LeaveApplication, 
    TrainingCategory, TrainingProgram, TrainingSession, TrainingEnrollment,
    EducationLevel, DocumentType, EmployeeEducation, EmployeeDocument,
    PerformanceCycle, PerformanceReview,
    PayrollPeriod, PayrollItem, ReportTemplate, ScheduledReport, ReportExecution,
    WorkSchedule, EmployeeSchedule, Attendance, AttendanceSession, AttendanceRequest, TimeSheet, AttendanceSettings,
    VendorStaff, ServiceAssignment, VendorStaffTraining
)


from .forms import EmployeeCreateForm, EmployeeUpdateForm


# Helper: resolve EmployeeProfile for a User
def resolve_employee_profile(user):
    """Return the EmployeeProfile for a User.

    New code uses the OneToOneField related_name 'profile'. Older code
    referenced 'employee_profile'. Support both to avoid AttributeError
    across the codebase.
    """
    return getattr(user, 'profile', None) or getattr(user, 'employee_profile', None)


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access certain views"""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


# ============================================================================
# DASHBOARD VIEWS
# ============================================================================

class HRMSDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics
        context.update({
            'total_employees': EmployeeProfile.objects.filter(status='active').count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'pending_leaves': LeaveApplication.objects.filter(status='pending').count(),
            'active_training_programs': TrainingProgram.objects.filter(is_active=True).count(),
        })
        
        # Recent activities
        context['recent_employees'] = EmployeeProfile.objects.select_related(
            'user', 'department', 'position'
        ).order_by('-created_at')[:5]
        
        context['pending_leave_applications'] = LeaveApplication.objects.select_related(
            'employee__user', 'leave_type'
        ).filter(status='pending').order_by('-applied_on')[:5]
        
        context['upcoming_training'] = TrainingSession.objects.select_related(
            'program'
        ).filter(start_date__gte=timezone.now()).order_by('start_date')[:5]
        
        return context


# ============================================================================
# EMPLOYEE MANAGEMENT VIEWS
# ============================================================================

class EmployeeListView(LoginRequiredMixin, ListView):
    model = EmployeeProfile
    template_name = 'hrms/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = EmployeeProfile.objects.select_related(
            'user', 'department', 'position', 'grade'
        ).order_by('user__first_name')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Department filter
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['search_term'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeProfile
    template_name = 'hrms/employees/detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Get employee's leave balances
        context['leave_balances'] = LeaveBalance.objects.filter(
            employee=employee,
            year=timezone.now().year
        ).select_related('leave_type')
        
        # Get recent leave applications
        context['recent_leaves'] = LeaveApplication.objects.filter(
            employee=employee
        ).order_by('-applied_on')[:5]
        
        # Get training enrollments
        context['training_enrollments'] = TrainingEnrollment.objects.filter(
            employee=employee
        ).select_related('session__program').order_by('-enrollment_date')[:5]
        
        return context


class EmployeeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = EmployeeProfile
    template_name = 'hrms/employees/form.html'
    form_class = EmployeeCreateForm
    success_url = reverse_lazy('hrms:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Employee'
        # Add education levels and document types for the frontend
        context['education_levels'] = EducationLevel.objects.filter(is_active=True).order_by('level_order')
        context['document_types'] = DocumentType.objects.filter(is_active=True).order_by('category', 'name')
        return context

    def form_valid(self, form):
        # Save the employee profile first
        self.object = form.save()
        
        # Create User account
        first_name = form.cleaned_data.get('first_name')
        last_name = form.cleaned_data.get('last_name')
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        
        if first_name and last_name and username and email:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            self.object.user = user
            self.object.save()
        
        messages.success(self.request, 'Employee created successfully.')
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = EmployeeProfile
    template_name = 'hrms/employees/form.html'
    form_class = EmployeeUpdateForm
    success_url = reverse_lazy('hrms:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Employee'
        # Add education levels and document types for the frontend
        context['education_levels'] = EducationLevel.objects.filter(is_active=True).order_by('level_order')
        context['document_types'] = DocumentType.objects.filter(is_active=True).order_by('category', 'name')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Employee updated successfully.')
        return super().form_valid(form)


class EmployeeProfileView(LoginRequiredMixin, DetailView):
    model = EmployeeProfile
    template_name = 'hrms/employees/profile.html'
    context_object_name = 'employee'


# ============================================================================
# DEPARTMENT MANAGEMENT VIEWS
# ============================================================================

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'hrms/departments/list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        return Department.objects.annotate(
            employee_count=Count('employees')
        ).order_by('name')


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'hrms/departments/detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.get_object()
        context['employees'] = EmployeeProfile.objects.filter(
            department=department,
            status='active'
        ).select_related('user', 'position')
        return context


class DepartmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Department
    template_name = 'hrms/departments/form.html'
    fields = ['name', 'code', 'description', 'budget', 'is_active']
    success_url = reverse_lazy('hrms:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department created successfully.')
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Department
    template_name = 'hrms/departments/form.html'
    fields = ['name', 'code', 'description', 'budget', 'is_active']
    success_url = reverse_lazy('hrms:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department updated successfully.')
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Department
    template_name = 'hrms/departments/confirm_delete.html'
    success_url = reverse_lazy('hrms:department_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Department deleted successfully.')
        return super().delete(request, *args, **kwargs)


class DepartmentBulkActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        ids = request.POST.getlist('ids')
        
        if not action or not ids:
            return JsonResponse({'success': False, 'message': 'Invalid request'})
        
        try:
            departments = Department.objects.filter(id__in=ids)
            count = departments.count()
            
            if action == 'activate':
                departments.update(is_active=True)
                message = f'Successfully activated {count} department(s)'
            elif action == 'deactivate':
                departments.update(is_active=False)
                message = f'Successfully deactivated {count} department(s)'
            elif action == 'delete':
                departments.delete()
                message = f'Successfully deleted {count} department(s)'
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
            
            return JsonResponse({'success': True, 'message': message})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# ============================================================================
# POSITION MANAGEMENT VIEWS
# ============================================================================

class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    template_name = 'hrms/positions/list.html'
    context_object_name = 'positions'

    def get_queryset(self):
        return Position.objects.select_related('department').annotate(
            employee_count=Count('employees')
        ).order_by('department__name', 'title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments_count'] = Department.objects.filter(is_active=True).count()
        return context


class PositionDetailView(LoginRequiredMixin, DetailView):
    model = Position
    template_name = 'hrms/positions/detail.html'
    context_object_name = 'position'


class PositionCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Position
    template_name = 'hrms/positions/form.html'
    fields = [
        'title', 'code', 'department', 'level', 'min_salary', 'max_salary',
        'description', 'requirements', 'responsibilities', 'is_active'
    ]
    success_url = reverse_lazy('hrms:position_list')


# ============================================================================
# LEAVE MANAGEMENT VIEWS
# ============================================================================

class LeaveApplicationListView(LoginRequiredMixin, ListView):
    model = LeaveApplication
    template_name = 'hrms/leaves/list.html'
    context_object_name = 'leave_applications'
    paginate_by = 20

    def get_queryset(self):
        queryset = LeaveApplication.objects.select_related(
            'employee__user', 'leave_type', 'approved_by'
        ).order_by('-applied_on')
        
        if not self.request.user.is_staff:
            # Non-staff users see only their own leave applications
            queryset = queryset.filter(employee__user=self.request.user)
            
        return queryset


class LeaveApplicationDetailView(LoginRequiredMixin, DetailView):
    model = LeaveApplication
    template_name = 'hrms/leaves/detail.html'
    context_object_name = 'leave_application'


class LeaveApplicationCreateView(LoginRequiredMixin, CreateView):
    model = LeaveApplication
    template_name = 'hrms/leaves/form.html'
    fields = ['leave_type', 'start_date', 'end_date', 'reason']
    success_url = reverse_lazy('hrms:leave_list')

    def form_valid(self, form):
        # Get the employee profile for the current user
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            form.instance.employee = employee
            form.instance.status = 'pending'
            # applied_on is auto_now_add=True, so it's set automatically
            
            # Calculate total days
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            form.instance.total_days = (end_date - start_date).days + 1
            
            messages.success(self.request, 'Leave application submitted successfully.')
            return super().form_valid(form)
        except EmployeeProfile.DoesNotExist:
            messages.error(self.request, 'Employee profile not found.')
            return redirect('hrms:dashboard')


class LeaveApprovalView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        leave_application = get_object_or_404(LeaveApplication, pk=pk)
        action = request.POST.get('action')
        
        if action == 'approve':
            leave_application.status = 'approved'
            leave_application.approved_by = request.user
            leave_application.approved_date = timezone.now().date()
            messages.success(request, 'Leave application approved.')
        elif action == 'reject':
            leave_application.status = 'rejected'
            leave_application.approved_by = request.user
            leave_application.approved_date = timezone.now().date()
            messages.success(request, 'Leave application rejected.')
            
        leave_application.save()
        return redirect('hrms:leave_detail', pk=pk)


class LeaveBalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/leaves/balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            context['leave_balances'] = LeaveBalance.objects.filter(
                employee=employee,
                year=timezone.now().year
            ).select_related('leave_type')
        except EmployeeProfile.DoesNotExist:
            context['leave_balances'] = []
        return context


# ============================================================================
# TRAINING MANAGEMENT VIEWS
# ============================================================================

class TrainingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/training/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_programs'] = TrainingProgram.objects.filter(is_active=True).count()
        context['upcoming_sessions'] = TrainingSession.objects.filter(
            start_date__gte=timezone.now()
        ).order_by('start_date')[:5]
        
        # User's enrollments if they're an employee
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            context['my_enrollments'] = TrainingEnrollment.objects.filter(
                employee=employee
            ).select_related('session__program')[:5]
        except EmployeeProfile.DoesNotExist:
            context['my_enrollments'] = []
            
        return context


class TrainingProgramListView(LoginRequiredMixin, ListView):
    model = TrainingProgram
    template_name = 'hrms/training/programs.html'
    context_object_name = 'programs'
    paginate_by = 12

    def get_queryset(self):
        return TrainingProgram.objects.filter(is_active=True).select_related('category')


class TrainingProgramDetailView(LoginRequiredMixin, DetailView):
    model = TrainingProgram
    template_name = 'hrms/training/program_detail.html'
    context_object_name = 'program'


class TrainingEnrollmentView(LoginRequiredMixin, View):
    def post(self, request, program_id):
        try:
            employee = EmployeeProfile.objects.get(user=request.user)
            program = get_object_or_404(TrainingProgram, id=program_id, is_active=True)
            
            enrollment, created = TrainingEnrollment.objects.get_or_create(
                employee=employee,
                program=program,
                defaults={
                    'enrollment_date': timezone.now().date(),
                    'status': 'enrolled'
                }
            )
            
            if created:
                messages.success(request, f'Successfully enrolled in {program.title}')
            else:
                messages.info(request, f'You are already enrolled in {program.title}')
                
        except EmployeeProfile.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            
        return redirect('hrms:training_program_detail', pk=program_id)


class MyTrainingsView(LoginRequiredMixin, ListView):
    model = TrainingEnrollment
    template_name = 'hrms/training/my_trainings.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            return TrainingEnrollment.objects.filter(
                employee=employee
            ).select_related('session__program', 'session__program__category').order_by('-enrollment_date')
        except EmployeeProfile.DoesNotExist:
            return TrainingEnrollment.objects.none()


class TrainingProgramCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = TrainingProgram
    template_name = 'hrms/training/form.html'
    fields = [
        'title', 'code', 'category', 'description', 'objectives', 'prerequisites',
        'duration_hours', 'max_participants', 'training_type', 'level',
        'cost_per_participant', 'materials', 'is_mandatory', 'is_active'
    ]
    success_url = reverse_lazy('hrms:training_programs')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Training program created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Training Program'
        return context


class TrainingProgramUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = TrainingProgram
    template_name = 'hrms/training/form.html'
    fields = [
        'title', 'code', 'category', 'description', 'objectives', 'prerequisites',
        'duration_hours', 'max_participants', 'training_type', 'level',
        'cost_per_participant', 'materials', 'is_mandatory', 'is_active'
    ]
    success_url = reverse_lazy('hrms:training_programs')

    def form_valid(self, form):
        messages.success(self.request, 'Training program updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Training Program'
        return context


# ============================================================================
# PERFORMANCE MANAGEMENT VIEWS
# ============================================================================

class PerformanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/performance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active performance cycles
        context['active_cycles'] = PerformanceCycle.objects.filter(
            status='active'
        ).order_by('-start_date')
        
        # User's performance reviews if they're an employee
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            context['my_reviews'] = PerformanceReview.objects.filter(
                employee=employee
            ).order_by('-review_period_start')[:5]
        except EmployeeProfile.DoesNotExist:
            context['my_reviews'] = []
            
        return context


class PerformanceReviewListView(LoginRequiredMixin, ListView):
    model = PerformanceReview
    template_name = 'hrms/performance/reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        queryset = PerformanceReview.objects.select_related(
            'employee__user', 'reviewer'
        ).order_by('-review_period_start')
        
        if not self.request.user.is_staff:
            # Non-staff users see only their own reviews
            queryset = queryset.filter(employee__user=self.request.user)
            
        return queryset


class PerformanceReviewDetailView(LoginRequiredMixin, DetailView):
    model = PerformanceReview
    template_name = 'hrms/performance/review_detail.html'
    context_object_name = 'review'


# ============================================================================
# PAYROLL MANAGEMENT VIEWS
# ============================================================================

class PayrollDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/payroll/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current month
        current_month = timezone.now().replace(day=1)
        
        # Basic statistics
        context['stats'] = {
            'total_payroll': PayrollItem.objects.filter(
                payroll_period__start_date__gte=current_month
            ).aggregate(total=Sum('net_salary'))['total'] or 0,
            'employees_paid': PayrollItem.objects.filter(
                payroll_period__start_date__gte=current_month
            ).values('employee').distinct().count(),
            'average_salary': PayrollItem.objects.filter(
                payroll_period__start_date__gte=current_month
            ).aggregate(avg=Avg('net_salary'))['avg'] or 0,
            'pending_approvals': PayrollItem.objects.filter(
                status='pending'
            ).count()
        }
        
        # Recent payroll entries
        context['payroll_entries'] = PayrollItem.objects.select_related(
            'employee__user', 'employee__department', 'payroll_period'
        ).order_by('-created_at')[:20]
        
        # Monthly summary
        monthly_items = PayrollItem.objects.filter(
            payroll_period__start_date__gte=current_month
        )
        
        # Calculate total allowances from individual allowance fields
        housing_total = monthly_items.aggregate(total=Sum('housing_allowance'))['total'] or 0
        transport_total = monthly_items.aggregate(total=Sum('transport_allowance'))['total'] or 0
        overtime_total = monthly_items.aggregate(total=Sum('overtime_amount'))['total'] or 0
        bonus_total = monthly_items.aggregate(total=Sum('bonus'))['total'] or 0
        other_earnings_total = monthly_items.aggregate(total=Sum('other_earnings'))['total'] or 0
        
        context['monthly_summary'] = {
            'basic_salary': monthly_items.aggregate(total=Sum('basic_salary'))['total'] or 0,
            'allowances': housing_total + transport_total + overtime_total + bonus_total + other_earnings_total,
            'deductions': monthly_items.aggregate(total=Sum('total_deductions'))['total'] or 0,
            'net_total': monthly_items.aggregate(total=Sum('net_salary'))['total'] or 0,
        }
        
        # Department summary
        context['department_summary'] = Department.objects.annotate(
            employee_count=Count('employees'),
            total_payroll=Sum('employees__payroll_items__net_salary')
        ).filter(employee_count__gt=0)
        
        # Departments for filter
        context['departments'] = Department.objects.all()
        
        # Months for filter
        context['months'] = [
            {'value': '01', 'label': 'January'},
            {'value': '02', 'label': 'February'},
            {'value': '03', 'label': 'March'},
            {'value': '04', 'label': 'April'},
            {'value': '05', 'label': 'May'},
            {'value': '06', 'label': 'June'},
            {'value': '07', 'label': 'July'},
            {'value': '08', 'label': 'August'},
            {'value': '09', 'label': 'September'},
            {'value': '10', 'label': 'October'},
            {'value': '11', 'label': 'November'},
            {'value': '12', 'label': 'December'},
        ]
        
        context['current_month'] = timezone.now().month
        
        # Current period
        context['current_period'] = PayrollPeriod.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        # Upcoming payroll dates (sample data)
        context['upcoming_payroll_dates'] = [
            {
                'day': '15',
                'type': 'Salary Processing',
                'date': timezone.now() + timezone.timedelta(days=7),
                'description': 'Monthly salary processing deadline'
            },
            {
                'day': '25',
                'type': 'Payment Release',
                'date': timezone.now() + timezone.timedelta(days=17),
                'description': 'Salary payment to employees'
            }
        ]
        
        return context


class PayrollPeriodListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = PayrollPeriod
    template_name = 'hrms/payroll/periods.html'
    context_object_name = 'periods'
    paginate_by = 12

    def get_queryset(self):
        return PayrollPeriod.objects.annotate(
            total_items=Count('payroll_items')
        ).order_by('-end_date')


class PayrollPeriodDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = PayrollPeriod
    template_name = 'hrms/payroll/period_detail.html'
    context_object_name = 'period'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.get_object()
        context['payroll_items'] = PayrollItem.objects.filter(
            payroll_period=period
        ).select_related('employee__user').order_by('employee__user__first_name')
        return context


class MyPayslipsView(LoginRequiredMixin, ListView):
    model = PayrollItem
    template_name = 'hrms/payroll/my_payslips.html'
    context_object_name = 'payslips'
    paginate_by = 12

    def get_queryset(self):
        try:
            employee = EmployeeProfile.objects.get(user=self.request.user)
            return PayrollItem.objects.filter(
                employee=employee
            ).select_related('payroll_period').order_by('-payroll_period__end_date')
        except EmployeeProfile.DoesNotExist:
            return PayrollItem.objects.none()


class PayrollExportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Handle payroll data export in various formats"""
    
    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('format', 'excel')
        
        if export_format == 'excel':
            return self.export_excel()
        elif export_format == 'pdf':
            return self.export_pdf()
        else:
            messages.error(request, 'Invalid export format requested.')
            return redirect('hrms:payroll_dashboard')
    
    def export_excel(self):
        from django.http import HttpResponse
        import io
        import xlsxwriter
        
        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Payroll Data')
        
        # Add headers
        headers = ['Employee', 'Department', 'Period', 'Basic Salary (QAR)', 'Total Earnings (QAR)', 'Total Deductions (QAR)', 'Net Pay (QAR)']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Add data
        payroll_items = PayrollItem.objects.select_related(
            'employee__user', 'employee__department', 'payroll_period'
        ).order_by('-payroll_period__end_date')
        
        for row, item in enumerate(payroll_items, 1):
            worksheet.write(row, 0, item.employee.user.get_full_name())
            worksheet.write(row, 1, item.employee.department.name if item.employee.department else 'N/A')
            worksheet.write(row, 2, f"{item.payroll_period.start_date} to {item.payroll_period.end_date}")
            worksheet.write(row, 3, float(item.basic_salary))
            worksheet.write(row, 4, float(item.total_earnings))
            worksheet.write(row, 5, float(item.total_deductions))
            worksheet.write(row, 6, float(item.net_pay))
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="payroll_data.xlsx"'
        return response
    
    def export_pdf(self):
        from django.http import HttpResponse
        from django.template.loader import get_template
        from django.template import Context
        
        # For now, return a simple message - PDF export would need reportlab
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="payroll_data.pdf"'
        
        # Simple text response for now
        response.write(b'PDF export functionality coming soon!')
        return response


class PayrollCreateView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Placeholder for payroll creation functionality"""
    template_name = 'hrms/payroll/create.html'


class PayrollDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Placeholder for payroll detail view"""
    model = PayrollItem
    template_name = 'hrms/payroll/detail.html'
    context_object_name = 'payroll'


class PayrollUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Placeholder for payroll update functionality"""
    model = PayrollItem
    template_name = 'hrms/payroll/update.html'
    fields = ['basic_salary', 'allowances', 'deductions']


class PayrollSlipView(LoginRequiredMixin, DetailView):
    """Placeholder for payroll slip generation"""
    model = PayrollItem
    template_name = 'hrms/payroll/slip.html'
    context_object_name = 'payroll'


class PayrollBulkProcessView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Placeholder for bulk payroll processing"""
    template_name = 'hrms/payroll/bulk_process.html'


class PayrollBulkActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Placeholder for bulk payroll actions"""
    
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        return JsonResponse({'status': 'success', 'message': 'Bulk action completed'})


class PayrollApprovePendingView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Placeholder for pending payroll approvals"""
    template_name = 'hrms/payroll/approve_pending.html'


class PayrollReportsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Placeholder for payroll reports"""
    template_name = 'hrms/payroll/reports.html'


class PayrollSettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Placeholder for payroll settings"""
    template_name = 'hrms/payroll/settings.html'


# ============================================================================
# REPORTS VIEWS
# ============================================================================

class ReportsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics for reports
        context['stats'] = {
            'total_employees': EmployeeProfile.objects.filter(status='active').count(),
            'departments': Department.objects.filter(is_active=True).count(),
            'this_month_leaves': LeaveApplication.objects.filter(
                applied_on__month=timezone.now().month,
                applied_on__year=timezone.now().year
            ).count(),
            'active_training': TrainingProgram.objects.filter(is_active=True).count(),
        }
        
        return context


class AnalyticsDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Employee analytics
        total_employees = EmployeeProfile.objects.filter(status='active').count()
        context['total_employees'] = total_employees
        
        # Department analytics
        departments = Department.objects.filter(is_active=True).annotate(
            employee_count=Count('employees')
        ).values('name', 'employee_count')
        context['department_data'] = list(departments)
        
        # Leave analytics
        current_year = timezone.now().year
        leave_stats = LeaveApplication.objects.filter(
            applied_on__year=current_year
        ).aggregate(
            total_applications=Count('id'),
            approved_applications=Count('id', filter=Q(status='approved')),
            pending_applications=Count('id', filter=Q(status='pending'))
        )
        context['leave_stats'] = leave_stats
        
        # Training analytics
        training_stats = TrainingEnrollment.objects.aggregate(
            total_enrollments=Count('id'),
            completed_enrollments=Count('id', filter=Q(completion_status='completed')),
            in_progress_enrollments=Count('id', filter=Q(completion_status='enrolled'))
        )
        context['training_stats'] = training_stats
        
        # Payroll analytics (if user has permission)
        if self.request.user.is_superuser:
            current_month = timezone.now().replace(day=1)
            payroll_queryset = PayrollItem.objects.filter(
                payroll_period__start_date__gte=current_month
            )
            
            # Calculate payroll stats safely
            total_payroll = payroll_queryset.aggregate(total=Sum('net_salary'))['total'] or 0
            employee_count = payroll_queryset.values('employee').distinct().count()
            avg_salary = total_payroll / employee_count if employee_count > 0 else 0
            
            payroll_stats = {
                'total_payroll': total_payroll,
                'avg_salary': avg_salary,
                'employee_count': employee_count
            }
            context['payroll_stats'] = payroll_stats
        
        return context


class EmployeeAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/analytics/employee_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Employee distribution by department
        dept_distribution = EmployeeProfile.objects.filter(status='active').values(
            'department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        context['dept_distribution'] = dept_distribution
        
        # Employee distribution by gender
        gender_distribution = EmployeeProfile.objects.filter(status='active').values(
            'gender'
        ).annotate(
            count=Count('id')
        )
        context['gender_distribution'] = gender_distribution
        
        # Age distribution
        today = timezone.now().date()
        employees = EmployeeProfile.objects.filter(status='active', date_of_birth__isnull=False)
        age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '55+': 0}
        
        for emp in employees:
            age = today.year - emp.date_of_birth.year
            if age <= 25:
                age_groups['18-25'] += 1
            elif age <= 35:
                age_groups['26-35'] += 1
            elif age <= 45:
                age_groups['36-45'] += 1
            elif age <= 55:
                age_groups['46-55'] += 1
            else:
                age_groups['55+'] += 1
        
        context['age_distribution'] = age_groups
        
        # Salary analysis
        salary_stats = EmployeeProfile.objects.filter(status='active').aggregate(
            avg_basic=Sum('basic_salary') / Count('id'),
            min_salary=Min('basic_salary'),
            max_salary=Max('basic_salary')
        )
        context['salary_stats'] = salary_stats
        
        return context


class LeaveAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/analytics/leave_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = timezone.now().year
        
        # Monthly leave trends
        monthly_leaves = LeaveApplication.objects.filter(
            applied_on__year=current_year
        ).extra(
            select={'month': 'EXTRACT(month FROM applied_on)'}
        ).values('month').annotate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
            pending=Count('id', filter=Q(status='pending'))
        ).order_by('month')
        context['monthly_leaves'] = monthly_leaves
        
        # Leave type analysis
        leave_type_stats = LeaveApplication.objects.filter(
            applied_on__year=current_year
        ).values(
            'leave_type__name'
        ).annotate(
            total=Count('id'),
            avg_days=Sum('total_days') / Count('id')
        ).order_by('-total')
        context['leave_type_stats'] = leave_type_stats
        
        # Department-wise leave analysis
        dept_leave_stats = LeaveApplication.objects.filter(
            applied_on__year=current_year
        ).values(
            'employee__department__name'
        ).annotate(
            total_applications=Count('id'),
            total_days=Sum('total_days'),
            avg_days_per_employee=Sum('total_days') / Count('employee', distinct=True)
        ).order_by('-total_applications')
        context['dept_leave_stats'] = dept_leave_stats
        
        return context


class TrainingAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/analytics/training_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Training completion rates by category
        category_stats = TrainingCategory.objects.annotate(
            total_programs=Count('programs'),
            total_enrollments=Count('programs__enrollments'),
            completed_enrollments=Count('programs__enrollments', filter=Q(programs__enrollments__status='completed'))
        ).values('name', 'total_programs', 'total_enrollments', 'completed_enrollments')
        context['category_stats'] = category_stats
        
        # Monthly training enrollments
        current_year = timezone.now().year
        monthly_enrollments = TrainingEnrollment.objects.filter(
            enrollment_date__year=current_year
        ).extra(
            select={'month': 'EXTRACT(month FROM enrollment_date)'}
        ).values('month').annotate(
            total=Count('id')
        ).order_by('month')
        context['monthly_enrollments'] = monthly_enrollments
        
        # Popular training programs
        popular_programs = TrainingProgram.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]
        context['popular_programs'] = popular_programs
        
        # Department-wise training participation
        dept_training_stats = EmployeeProfile.objects.filter(status='active').values(
            'department__name'
        ).annotate(
            total_employees=Count('id'),
            trained_employees=Count('training_enrollments', distinct=True),
            participation_rate=Count('training_enrollments', distinct=True) * 100.0 / Count('id')
        ).order_by('-participation_rate')
        context['dept_training_stats'] = dept_training_stats
        
        return context


class PayrollAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/analytics/payroll_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = timezone.now().year
        
        # Monthly payroll summary
        monthly_payroll = PayrollItem.objects.filter(
            payroll_period__start_date__year=current_year
        ).values(
            'payroll_period__name'
        ).annotate(
            total_gross=Sum('gross_salary'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary'),
            employee_count=Count('employee', distinct=True)
        ).order_by('payroll_period__start_date')
        context['monthly_payroll'] = monthly_payroll
        
        # Department-wise payroll analysis
        dept_payroll = PayrollItem.objects.values(
            'employee__department__name'
        ).annotate(
            total_payroll=Sum('net_salary'),
            employee_count=Count('employee', distinct=True),
            avg_salary=Sum('net_salary') / Count('employee', distinct=True)
        ).order_by('-total_payroll')
        context['dept_payroll'] = dept_payroll
        
        # Salary distribution
        salary_ranges = {
            '0-30k': 0, '30k-50k': 0, '50k-70k': 0, '70k-100k': 0, '100k+': 0
        }
        
        employees = EmployeeProfile.objects.filter(status='active')
        for emp in employees:
            total_salary = (emp.basic_salary or 0) + (emp.housing_allowance or 0) + \
                          (emp.transport_allowance or 0) + (emp.other_allowances or 0)
            
            if total_salary < 30000:
                salary_ranges['0-30k'] += 1
            elif total_salary < 50000:
                salary_ranges['30k-50k'] += 1
            elif total_salary < 70000:
                salary_ranges['50k-70k'] += 1
            elif total_salary < 100000:
                salary_ranges['70k-100k'] += 1
            else:
                salary_ranges['100k+'] += 1
        
        context['salary_ranges'] = salary_ranges
        
        return context


class EmployeeReportView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = EmployeeProfile
    template_name = 'hrms/reports/employee_report.html'
    context_object_name = 'employees'

    def get_queryset(self):
        queryset = EmployeeProfile.objects.select_related(
            'user', 'department', 'position', 'grade'
        ).filter(status='active').order_by('department__name', 'user__first_name')
        
        # Apply filters from GET parameters
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['active_count'] = EmployeeProfile.objects.filter(status='active').count()
        context['department_count'] = Department.objects.filter(is_active=True).count()
        context['new_this_month'] = EmployeeProfile.objects.filter(
            hire_date__month=timezone.now().month,
            hire_date__year=timezone.now().year
        ).count()
        return context


class EmployeeRosterReportView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = EmployeeProfile
    template_name = 'hrms/reports/employee_roster.html'
    context_object_name = 'employees'
    paginate_by = 50

    def get_queryset(self):
        queryset = EmployeeProfile.objects.select_related(
            'user', 'department', 'position', 'grade'
        ).filter(status='active').order_by('department__name', 'user__first_name')
        
        # Add filtering by department if requested
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Add search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all().order_by('name')
        context['selected_department'] = self.request.GET.get('department', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class AttendanceReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/reports/attendance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add attendance report logic here
        return context


class PayrollReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'hrms/reports/payroll_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        period_type = self.request.GET.get('period_type', 'monthly')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year', timezone.now().year)
        department_id = self.request.GET.get('department')
        
        # Get payroll items based on filters
        payroll_items = PayrollItem.objects.select_related(
            'employee__user', 'employee__department', 'payroll_period'
        ).all()
        
        if department_id:
            payroll_items = payroll_items.filter(employee__department_id=department_id)
        
        if month and year:
            payroll_items = payroll_items.filter(
                payroll_period__start_date__month=month,
                payroll_period__start_date__year=year
            )
        
        # Get latest payroll period
        latest_period = PayrollPeriod.objects.order_by('-end_date').first()
        if latest_period:
            context['payroll_summary'] = PayrollItem.objects.filter(
                payroll_period=latest_period
            ).aggregate(
                total_basic=Sum('basic_salary'),
                total_allowances=Sum(F('housing_allowance') + F('transport_allowance')),
                total_gross=Sum('gross_salary'),
                total_deductions=Sum('total_deductions'),
                total_net=Sum('net_salary')
            )
            context['latest_period'] = latest_period
            context['payroll_count'] = PayrollItem.objects.filter(
                payroll_period=latest_period
            ).count()
        
        context['payroll_items'] = payroll_items[:100]  # Limit for performance
        context['departments'] = Department.objects.filter(is_active=True)
        context['years'] = range(2020, timezone.now().year + 2)
        
        return context


# ============================================================================
# API VIEWS FOR AJAX
# ============================================================================

@login_required
def get_department_positions(request, dept_id):
    """API endpoint to get positions for a specific department"""
    positions = Position.objects.filter(
        department_id=dept_id, 
        is_active=True
    ).values('id', 'title')
    return JsonResponse({'positions': list(positions)})


@login_required
def get_employee_leave_balance(request, emp_id):
    """API endpoint to get leave balance for an employee"""
    try:
        employee = EmployeeProfile.objects.get(id=emp_id)
        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=timezone.now().year
        ).select_related('leave_type').values(
            'leave_type__name',
            'entitled_days',
            'used_days',
            'pending_days'
        )
        return JsonResponse({'balances': list(balances)})
    except EmployeeProfile.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)


# =============================================================================
# CUSTOM REPORTS VIEWS
# =============================================================================

class CustomReportListView(LoginRequiredMixin, ListView):
    """List all custom report templates"""
    model = ReportTemplate
    template_name = 'hrms/reports/custom_report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = ReportTemplate.objects.filter(is_active=True)
        
        # Filter based on access permissions
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(is_public=True) |
                Q(created_by=user) |
                Q(allowed_users=user) |
                Q(allowed_departments__in=user.employeeprofile.department.id if hasattr(user, 'employeeprofile') else [])
            ).distinct()
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_reports'] = self.get_queryset().count()
        context['my_reports'] = self.get_queryset().filter(created_by=self.request.user).count()
        return context


class CustomReportCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create a new custom report template"""
    model = ReportTemplate
    template_name = 'hrms/reports/custom_report_form.html'
    fields = ['name', 'description', 'report_type', 'fields', 'filters', 'grouping', 
              'sorting', 'export_formats', 'chart_config', 'is_public', 'allowed_users', 
              'allowed_departments']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_fields'] = self.get_available_fields()
        context['departments'] = Department.objects.filter(is_active=True)
        context['users'] = User.objects.filter(is_active=True)
        return context

    def get_available_fields(self):
        """Get available fields for different report types"""
        return {
            'employee': ['user__first_name', 'user__last_name', 'employee_id', 'department__name', 
                        'position__title', 'hire_date', 'basic_salary', 'status'],
            'payroll': ['employee__user__first_name', 'employee__user__last_name', 'basic_salary', 
                       'gross_salary', 'net_salary', 'payroll_period__name'],
            'attendance': ['employee__user__first_name', 'date', 'clock_in', 'clock_out', 'hours_worked'],
            'leave': ['employee__user__first_name', 'leave_type__name', 'start_date', 'end_date', 'days', 'status'],
        }


class CustomReportDetailView(LoginRequiredMixin, DetailView):
    """View and execute a custom report"""
    model = ReportTemplate
    template_name = 'hrms/reports/custom_report_detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get report data based on type and filters
        report_data = self.get_report_data()
        context['report_data'] = report_data
        context['executions'] = ReportExecution.objects.filter(
            report_template=self.object
        ).order_by('-started_at')[:10]
        
        return context

    def get_report_data(self):
        """Generate report data based on template configuration"""
        report = self.object
        
        if report.report_type == 'employee':
            queryset = EmployeeProfile.objects.all()
        elif report.report_type == 'payroll':
            queryset = PayrollItem.objects.all()
        elif report.report_type == 'attendance':
            # For now, use PayrollItem as a placeholder since Attendance model doesn't exist
            queryset = PayrollItem.objects.all()
        elif report.report_type == 'leave':
            queryset = LeaveApplication.objects.all()
        else:
            queryset = EmployeeProfile.objects.none()

        # Apply filters from template
        if report.filters:
            for field, value in report.filters.items():
                if value:
                    queryset = queryset.filter(**{field: value})

        # Apply sorting
        if report.sorting:
            order_by = report.sorting.get('order_by', [])
            if order_by:
                queryset = queryset.order_by(*order_by)

        return queryset[:100]  # Limit to 100 records for performance


class ScheduledReportListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all scheduled reports"""
    model = ScheduledReport
    template_name = 'hrms/reports/scheduled_report_list.html'
    context_object_name = 'scheduled_reports'
    paginate_by = 20

    def get_queryset(self):
        return ScheduledReport.objects.select_related('report_template', 'created_by').order_by('-created_at')


class ScheduledReportCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create a new scheduled report"""
    model = ScheduledReport
    template_name = 'hrms/reports/scheduled_report_form.html'
    fields = ['name', 'description', 'report_template', 'frequency', 'day_of_week', 
              'day_of_month', 'time_of_day', 'delivery_method', 'email_recipients', 
              'email_subject', 'email_body', 'date_range_type', 'is_active']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_templates'] = ReportTemplate.objects.filter(is_active=True)
        return context


class ReportDownloadView(LoginRequiredMixin, View):
    """Download generated report files"""
    
    def get(self, request, pk):
        try:
            execution = ReportExecution.objects.get(pk=pk)
            
            # Check permissions
            if not request.user.is_superuser and execution.generated_by != request.user:
                return HttpResponseForbidden("You don't have permission to download this report")
            
            # Update download statistics
            execution.download_count += 1
            execution.last_downloaded = timezone.now()
            execution.save()
            
            # Serve the file
            if execution.file_path and os.path.exists(execution.file_path):
                with open(execution.file_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(execution.file_path)}"'
                    return response
            else:
                return HttpResponseNotFound("Report file not found")
                
        except ReportExecution.DoesNotExist:
            return HttpResponseNotFound("Report execution not found")


@login_required
def export_report_ajax(request):
    """AJAX endpoint for exporting reports"""
    if request.method == 'POST':
        import json
        
        data = json.loads(request.body)
        report_type = data.get('report_type')
        export_format = data.get('format', 'csv')
        period = data.get('period', 'monthly')
        filters = data.get('filters', {})
        
        try:
            # Create report execution record
            execution = ReportExecution.objects.create(
                report_template_id=data.get('template_id') if data.get('template_id') else None,
                status='running',
                export_format=export_format,
                parameters=data,
                generated_by=request.user
            )
            
            # Generate the report (this would typically be done async)
            file_path = generate_report_file(report_type, export_format, period, filters, execution.id)
            
            # Update execution record
            execution.status = 'completed'
            execution.file_path = file_path
            execution.completed_at = timezone.now()
            execution.save()
            
            return JsonResponse({
                'success': True,
                'execution_id': execution.id,
                'download_url': execution.get_download_url()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def generate_report_file(report_type, export_format, period, filters, execution_id):
    """Generate report file (CSV, PDF, Excel)"""
    import csv
    import io
    import os
    from django.conf import settings
    from django.template.loader import render_to_string
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate filename
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{report_type}_{period}_{timestamp}_{execution_id}.{export_format}"
    file_path = os.path.join(reports_dir, filename)
    
    # Get report data
    if report_type == 'employee':
        queryset = EmployeeProfile.objects.select_related('user', 'department', 'position')
    elif report_type == 'payroll':
        queryset = PayrollItem.objects.select_related('employee__user', 'payroll_period')
    else:
        queryset = EmployeeProfile.objects.none()
    
    # Apply filters
    for field, value in filters.items():
        if value:
            queryset = queryset.filter(**{field: value})
    
    if export_format == 'csv':
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if report_type == 'employee':
                fieldnames = ['Employee ID', 'Name', 'Email', 'Department', 'Position', 'Hire Date', 'Salary', 'Status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for emp in queryset:
                    writer.writerow({
                        'Employee ID': emp.employee_id or '',
                        'Name': emp.user.get_full_name(),
                        'Email': emp.user.email,
                        'Department': emp.department.name if emp.department else '',
                        'Position': emp.position.title if emp.position else '',
                        'Hire Date': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                        'Salary': str(emp.basic_salary) if emp.basic_salary else '',
                        'Status': emp.status
                    })
            
            elif report_type == 'payroll':
                fieldnames = ['Employee', 'Period', 'Basic Salary', 'Gross Salary', 'Deductions', 'Net Salary', 'Status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in queryset:
                    writer.writerow({
                        'Employee': item.employee.user.get_full_name(),
                        'Period': item.payroll_period.name,
                        'Basic Salary': str(item.basic_salary),
                        'Gross Salary': str(item.gross_salary),
                        'Deductions': str(item.total_deductions),
                        'Net Salary': str(item.net_salary),
                        'Status': item.status
                    })
    
    elif export_format == 'pdf':
        # For PDF generation, you would typically use libraries like reportlab or weasyprint
        # This is a simplified implementation
        html_content = render_to_string('hrms/reports/pdf_template.html', {
            'report_type': report_type,
            'data': queryset,
            'period': period,
            'generated_at': timezone.now()
        })
        
        # Save as HTML for now (you can integrate proper PDF generation)
        with open(file_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        file_path = file_path.replace('.pdf', '.html')
    
    return file_path


class EmployeeProfileListView(LoginRequiredMixin, ListView):
    """Employee Profile Directory with grid and table views"""
    model = EmployeeProfile
    template_name = 'hrms/reports/employeeprofile_list.html'
    context_object_name = 'employees'
    paginate_by = 24

    def get_queryset(self):
        queryset = EmployeeProfile.objects.select_related(
            'user', 'department', 'position', 'grade'
        ).filter(status__in=['active', 'inactive'])
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        position_id = self.request.GET.get('position')
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply sorting
        sort_by = self.request.GET.get('sort_by', 'name')
        if sort_by == 'name':
            queryset = queryset.order_by('user__first_name', 'user__last_name')
        elif sort_by == 'department':
            queryset = queryset.order_by('department__name', 'user__first_name')
        elif sort_by == 'hire_date':
            queryset = queryset.order_by('-hire_date')
        elif sort_by == 'employee_id':
            queryset = queryset.order_by('employee_id')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['positions'] = Position.objects.filter(is_active=True)
        context['total_employees'] = EmployeeProfile.objects.count()
        return context


# =============================================================================
# TIME & ATTENDANCE VIEWS
# =============================================================================

class AttendanceDashboardView(LoginRequiredMixin, TemplateView):
    """Main attendance dashboard"""
    template_name = 'hrms/attendance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get today's attendance for current user
        today = timezone.now().date()
        try:
            employee = resolve_employee_profile(self.request.user)
            today_attendance = Attendance.objects.filter(
                employee=employee, 
                date=today
            ).first()
        except:
            employee = None
            today_attendance = None
        
        # Stats for admins
        if self.request.user.is_staff:
            context.update({
                'total_employees': EmployeeProfile.objects.count(),
                'present_today': Attendance.objects.filter(
                    date=today, 
                    status__in=['present', 'late', 'remote']
                ).count(),
                'absent_today': Attendance.objects.filter(
                    date=today, 
                    status='absent'
                ).count(),
                'late_today': Attendance.objects.filter(
                    date=today, 
                    status='late'
                ).count(),
                'pending_requests': AttendanceRequest.objects.filter(
                    status='pending'
                ).count(),
                'recent_attendance': Attendance.objects.select_related(
                    'employee__user'
                ).filter(date=today).order_by('-check_in')[:10]
            })
        
        context.update({
            'employee': employee,
            'today_attendance': today_attendance,
            'today': today,
            'schedules': WorkSchedule.objects.filter(is_active=True)
        })
        
        return context

class ClockInOutView(LoginRequiredMixin, View):
    """Handle clock in/out actions"""
    
    def get(self, request):
        """Show clock in/out page"""
        try:
            employee = resolve_employee_profile(request.user)
        except:
            messages.error(request, 'Employee profile not found. Please contact your administrator.')
            return redirect('hrms:dashboard')
        
        today = timezone.now().date()
        
        # Get today's attendance record if exists
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            attendance = None
        
        # Get office locations for location-based attendance
        office_locations = AttendanceSettings.objects.filter(is_active=True)
        
        context = {
            'employee': employee,
            'attendance': attendance,
            'office_locations': office_locations,
            'today': today,
            'current_time': timezone.now(),
        }
        
        return render(request, 'hrms/attendance/clock.html', context)
    
    def post(self, request):
        try:
            employee = resolve_employee_profile(request.user)
        except:
            return JsonResponse({
                'success': False, 
                'message': 'Employee profile not found.'
            })
        
        action = request.POST.get('action')  # 'clock_in' or 'clock_out'
        today = timezone.now().date()
        now = timezone.now()
        
        # Get or create today's attendance record
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                'scheduled_hours': employee.work_schedule.schedule.daily_hours if hasattr(employee, 'work_schedule') else 8.0
            }
        )
        
        # Handle clock in
        if action == 'clock_in':
            if attendance.check_in:
                return JsonResponse({
                    'success': False,
                    'message': 'Already clocked in today.'
                })
            
            attendance.check_in = now
            attendance.check_in_ip = self.get_client_ip(request)
            attendance.device_info = self.get_device_info(request)
            
            # Handle location if provided
            if request.POST.get('latitude') and request.POST.get('longitude'):
                attendance.check_in_location = {
                    'lat': float(request.POST.get('latitude')),
                    'lng': float(request.POST.get('longitude')),
                    'address': request.POST.get('address', '')
                }
            
            # Handle remote work
            attendance.is_remote = request.POST.get('is_remote') == 'true'
            
            message = f"Clocked in at {now.strftime('%H:%M')}"
            
        # Handle clock out
        elif action == 'clock_out':
            if not attendance.check_in:
                return JsonResponse({
                    'success': False,
                    'message': 'Must clock in first.'
                })
            
            if attendance.check_out:
                return JsonResponse({
                    'success': False,
                    'message': 'Already clocked out today.'
                })
            
            attendance.check_out = now
            attendance.check_out_ip = self.get_client_ip(request)
            
            # Handle location if provided
            if request.POST.get('latitude') and request.POST.get('longitude'):
                attendance.check_out_location = {
                    'lat': float(request.POST.get('latitude')),
                    'lng': float(request.POST.get('longitude')),
                    'address': request.POST.get('address', '')
                }
            
            message = f"Clocked out at {now.strftime('%H:%M')}"
        
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action.'
            })
        
        # Save attendance record (this will trigger auto-calculation)
        attendance.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'attendance': {
                'check_in': attendance.check_in.strftime('%H:%M') if attendance.check_in else None,
                'check_out': attendance.check_out.strftime('%H:%M') if attendance.check_out else None,
                'hours_worked': str(attendance.hours_worked or 0),
                'status': attendance.get_status_display(),
                'is_complete': attendance.is_complete
            }
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_info(self, request):
        """Get device information"""
        return {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
            'mobile': request.META.get('HTTP_SEC_CH_UA_MOBILE', ''),
        }

class AttendanceListView(LoginRequiredMixin, ListView):
    """List view for attendance records"""
    model = Attendance
    template_name = 'hrms/attendance/list.html'
    context_object_name = 'attendance_records'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related(
            'employee__user', 'employee__department'
        ).order_by('-date', '-check_in')
        
        # Filter by employee for non-staff users
        if not self.request.user.is_staff:
            try:
                employee = resolve_employee_profile(self.request.user)
                queryset = queryset.filter(employee=employee)
            except:
                return Attendance.objects.none()
        
        # Apply filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        employee_id = self.request.GET.get('employee')
        status = self.request.GET.get('status')
        department = self.request.GET.get('department')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if employee_id and self.request.user.is_staff:
            queryset = queryset.filter(employee__id=employee_id)
        if status:
            queryset = queryset.filter(status=status)
        if department and self.request.user.is_staff:
            queryset = queryset.filter(employee__department__id=department)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_staff:
            context['employees'] = EmployeeProfile.objects.select_related('user')
            context['departments'] = Department.objects.filter(is_active=True)
        
        context['status_choices'] = Attendance.STATUS_CHOICES
        return context

class AttendanceRequestCreateView(LoginRequiredMixin, CreateView):
    """Create attendance request"""
    model = AttendanceRequest
    template_name = 'hrms/attendance/request_form.html'
    fields = ['request_type', 'requested_date', 'requested_check_in', 'requested_check_out', 'reason', 'supporting_document']
    
    def form_valid(self, form):
        try:
            form.instance.employee = resolve_employee_profile(self.request.user)
        except:
            messages.error(self.request, 'Employee profile not found.')
            return self.form_invalid(form)
        
        messages.success(self.request, 'Attendance request submitted successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('hrms:attendance_requests')

class AttendanceRequestListView(LoginRequiredMixin, ListView):
    """List attendance requests"""
    model = AttendanceRequest
    template_name = 'hrms/attendance/request_list.html'
    context_object_name = 'requests'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = AttendanceRequest.objects.select_related(
            'employee__user', 'reviewed_by'
        ).order_by('-submitted_at')
        
        # Filter by employee for non-staff users
        if not self.request.user.is_staff:
            try:
                employee = resolve_employee_profile(self.request.user)
                queryset = queryset.filter(employee=employee)
            except:
                return AttendanceRequest.objects.none()
        
        # Apply filters
        status = self.request.GET.get('status')
        request_type = self.request.GET.get('request_type')
        
        if status:
            queryset = queryset.filter(status=status)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        return queryset

class WorkScheduleListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List work schedules"""
    model = WorkSchedule
    template_name = 'hrms/attendance/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20

class WorkScheduleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create work schedule"""
    model = WorkSchedule
    template_name = 'hrms/attendance/schedule_form.html'
    fields = ['name', 'schedule_type', 'description', 'start_time', 'end_time', 'break_duration', 'work_days', 'weekly_hours', 'overtime_after_hours', 'overtime_rate', 'late_grace_minutes', 'early_departure_minutes', 'require_location', 'location_radius']
    
    def get_success_url(self):
        return reverse('hrms:schedule_list')

class TimeSheetView(LoginRequiredMixin, TemplateView):
    """View employee timesheet"""
    template_name = 'hrms/attendance/timesheet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            employee = resolve_employee_profile(self.request.user)
        except:
            messages.error(self.request, 'Employee profile not found.')
            return context
        
        # Get date range (default to current week)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        date_from = self.request.GET.get('date_from', start_of_week)
        date_to = self.request.GET.get('date_to', end_of_week)
        
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Get attendance records for the period
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__range=[date_from, date_to]
        ).order_by('date')
        
        # Calculate summary
        total_scheduled = sum(record.scheduled_hours for record in attendance_records)
        total_worked = sum(record.hours_worked or 0 for record in attendance_records)
        total_overtime = sum(record.overtime_hours for record in attendance_records)
        
        context.update({
            'employee': employee,
            'attendance_records': attendance_records,
            'date_from': date_from,
            'date_to': date_to,
            'total_scheduled': total_scheduled,
            'total_worked': total_worked,
            'total_overtime': total_overtime,
            'attendance_percentage': round((total_worked / total_scheduled * 100) if total_scheduled > 0 else 0, 2)
        })
        
        return context

class AttendanceReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Comprehensive attendance reports"""
    template_name = 'hrms/attendance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        date_from = self.request.GET.get('date_from', thirty_days_ago)
        date_to = self.request.GET.get('date_to', today)
        
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Attendance statistics
        attendance_qs = Attendance.objects.filter(date__range=[date_from, date_to])
        
        stats = {
            'total_records': attendance_qs.count(),
            'present': attendance_qs.filter(status='present').count(),
            'absent': attendance_qs.filter(status='absent').count(),
            'late': attendance_qs.filter(status='late').count(),
            'early_departure': attendance_qs.filter(status='early_departure').count(),
            'remote': attendance_qs.filter(status='remote').count(),
            'half_day': attendance_qs.filter(status='half_day').count(),
        }
        
        # Department-wise breakdown
        from django.db.models import Count, Avg
        dept_stats = attendance_qs.values(
            'employee__department__name'
        ).annotate(
            total_records=Count('id'),
            avg_hours=Avg('hours_worked'),
            present_count=Count('id', filter=Q(status='present')),
            late_count=Count('id', filter=Q(status='late'))
        ).order_by('employee__department__name')
        
        context.update({
            'date_from': date_from,
            'date_to': date_to,
            'stats': stats,
            'dept_stats': dept_stats,
            'departments': Department.objects.filter(is_active=True)
        })
        
        return context


class MyAttendanceLogView(LoginRequiredMixin, ListView):
    """Employee's personal attendance history (My Log)"""
    model = Attendance
    template_name = 'hrms/attendance/my_log.html'
    context_object_name = 'attendance_records'
    paginate_by = 20

    def get_queryset(self):
        qs = Attendance.objects.select_related('employee__user').order_by('-date', '-check_in')

        # Non-staff users should only see their own records
        if not self.request.user.is_staff:
            try:
                employee = resolve_employee_profile(self.request.user)
                qs = qs.filter(employee=employee)
            except Exception:
                return Attendance.objects.none()

        # Optional filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        total = qs.count()
        present = qs.filter(status='present').count()

        context.update({
            'total_records': total,
            'present_days': present,
            'attendance_percentage': round((present / total * 100) if total else 0, 2),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'status_filter': self.request.GET.get('status', ''),
        })

        return context


# User Attendance Views and APIs

# User Attendance View
@login_required
def user_attendance_view(request):
    """Simple user interface for clock in/out"""
    return render(request, 'hrms/attendance/user_attendance.html')

# API endpoint for attendance status
@login_required
def attendance_status_api(request):
    """Get current attendance status for the user - Enhanced for multiple sessions

    Returns a default JSON payload if the user does not have an EmployeeProfile
    to avoid returning a 500 error to the frontend.
    """
    logger = logging.getLogger(__name__)

    try:
        # Prefer the safe helper which supports different relations
        employee_profile = resolve_employee_profile(request.user)
        if not employee_profile:
            logger.warning('Attendance status requested but EmployeeProfile not found for user %s', request.user)
            return JsonResponse({'error': 'Employee profile not found'}, status=404)

        today = timezone.now().date()

        # Get today's attendance record
        attendance = Attendance.objects.filter(
            employee=employee_profile,
            date=today
        ).first()

        # Check for ongoing session
        ongoing_session = AttendanceSession.objects.filter(
            employee=employee_profile,
            check_in__date=today,
            check_out__isnull=True
        ).first()

        status_data = {
            'isCheckedIn': False,
            'checkInTime': None,
            'checkOutTime': None,
            'hoursWorked': '0.00',
            'status': 'Not Started',
            'sessionsToday': [],
            'totalSessions': 0,
            'currentSession': None
        }

        if attendance:
            # If there's an ongoing session prefer that for checked-in state
            status_data['isCheckedIn'] = bool(ongoing_session) or (attendance.check_in and not attendance.check_out)
            if attendance.check_in:
                status_data['checkInTime'] = attendance.check_in.strftime('%H:%M')
            if attendance.check_out:
                status_data['checkOutTime'] = attendance.check_out.strftime('%H:%M')
                status_data['isCheckedIn'] = False
            status_data['hoursWorked'] = str(attendance.hours_worked or 0)

            # Get all sessions for today
            sessions = AttendanceSession.objects.filter(
                employee=employee_profile,
                check_in__date=today
            ).order_by('check_in')

            sessions_data = []
            for session in sessions:
                session_data = {
                    'id': session.id,
                    'checkIn': session.check_in.strftime('%H:%M'),
                    'checkOut': session.check_out.strftime('%H:%M') if session.check_out else None,
                    'sessionType': getattr(session, 'session_type', '') if not hasattr(session, 'get_session_type_display') else session.get_session_type_display(),
                    'reason': getattr(session, 'reason', None),
                    'duration': f"{session.duration_hours:.2f}h" if getattr(session, 'duration_hours', None) else ('Ongoing' if not session.check_out else '0.00h'),
                    'isOngoing': not bool(session.check_out)
                }
                sessions_data.append(session_data)

            status_data['sessionsToday'] = sessions_data
            status_data['totalSessions'] = sessions.count()

            # Set current session info
            if ongoing_session:
                status_data['currentSession'] = {
                    'id': ongoing_session.id,
                    'checkIn': ongoing_session.check_in.strftime('%H:%M'),
                    'sessionType': ongoing_session.get_session_type_display() if hasattr(ongoing_session, 'get_session_type_display') else getattr(ongoing_session, 'session_type', ''),
                    'reason': getattr(ongoing_session, 'reason', None)
                }
                status_data['checkInTime'] = ongoing_session.check_in.strftime('%H:%M')
                status_data['status'] = f'Working - {status_data["currentSession"]["sessionType"]}'
            else:
                # Check if there were any sessions today
                if sessions.exists():
                    last_session = sessions.last()
                    if last_session.check_out:
                        status_data['checkOutTime'] = last_session.check_out.strftime('%H:%M')
                        status_data['status'] = 'Available for Check-in'
                    else:
                        status_data['status'] = 'Error - Session without checkout'
                else:
                    status_data['status'] = 'Ready to Check-in'
        else:
            status_data['status'] = 'Ready to Check-in'

        return JsonResponse(status_data)
    except Exception as e:
        logger.exception('Error building attendance status for user %s', request.user)
        return JsonResponse({'error': str(e)}, status=500)

# Calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    return c * r

# API endpoint for check in
@login_required
@csrf_exempt
def check_in_api(request):
    """Handle check in with location verification"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        employee_profile = resolve_employee_profile(request.user)
        
        # Get user location
        user_lat = float(data.get('latitude'))
        user_lon = float(data.get('longitude'))
        
        # Get office locations from database
        office_locations = []
        for setting in AttendanceSettings.objects.filter(is_active=True):
            office_locations.append({
                'name': setting.office_name,
                'lat': float(setting.latitude),
                'lon': float(setting.longitude),
                'radius': setting.radius
            })
        
        # Check if user is within any office location
        is_within_office = False
        for office in office_locations:
            distance = calculate_distance(user_lat, user_lon, office['lat'], office['lon'])
            if distance <= office['radius']:
                is_within_office = True
                break
        
        if not is_within_office:
            return JsonResponse({
                'success': False, 
                'message': 'You must be within 50 meters of the office to check in'
            })
        
        # Check if already checked in today
        today = timezone.now().date()
        existing_attendance = Attendance.objects.filter(
            employee=employee_profile,
            date=today
        ).first()
        
        if existing_attendance and existing_attendance.check_in:
            return JsonResponse({
                'success': False, 
                'message': 'You are already checked in today'
            })
        
        # Create or update attendance record
        if existing_attendance:
            attendance = existing_attendance
        else:
            # Get employee schedule for today — prefer OneToOne relation if available
            employee_schedule = getattr(employee_profile, 'work_schedule', None)
            if not employee_schedule:
                # Fallback: find the most recent effective schedule
                employee_schedule = EmployeeSchedule.objects.filter(
                    employee=employee_profile,
                    effective_from__lte=today
                ).order_by('-effective_from').first()

            if employee_schedule:
                schedule = employee_schedule.schedule
                # Use the schedule's daily_hours property if available
                try:
                    scheduled_hours = Decimal(str(schedule.daily_hours))
                except Exception:
                    scheduled_hours = Decimal('8.00')
            else:
                scheduled_hours = Decimal('8.00')  # Default 8 hours
            
            attendance = Attendance.objects.create(
                employee=employee_profile,
                date=today,
                scheduled_hours=scheduled_hours
            )
        
        # Set check in time and location
        attendance.check_in = timezone.now()
        attendance.check_in_location = {
            'latitude': user_lat,
            'longitude': user_lon,
            'timestamp': timezone.now().isoformat()
        }
        attendance.status = 'present'
        attendance.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully checked in at {attendance.check_in.strftime("%H:%M")}',
            'checkInTime': attendance.check_in.strftime('%H:%M')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# API endpoint for check out
@login_required
@csrf_exempt
def check_out_api(request):
    """Handle check out with location verification"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        employee_profile = resolve_employee_profile(request.user)
        
        # Get user location
        user_lat = float(data.get('latitude'))
        user_lon = float(data.get('longitude'))
        
        # Get office locations from database
        office_locations = []
        for setting in AttendanceSettings.objects.filter(is_active=True):
            office_locations.append({
                'name': setting.office_name,
                'lat': float(setting.latitude),
                'lon': float(setting.longitude),
                'radius': setting.radius
            })
        
        # Check if user is within any office location
        is_within_office = False
        for office in office_locations:
            distance = calculate_distance(user_lat, user_lon, office['lat'], office['lon'])
            if distance <= office['radius']:
                is_within_office = True
                break
        
        if not is_within_office:
            return JsonResponse({
                'success': False, 
                'message': 'You must be within 50 meters of the office to check out'
            })
        
        # Get today's attendance
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            employee=employee_profile,
            date=today
        ).first()
        
        if not attendance or not attendance.check_in:
            return JsonResponse({
                'success': False, 
                'message': 'You must check in first'
            })
        
        if attendance.check_out:
            return JsonResponse({
                'success': False, 
                'message': 'You have already checked out today'
            })
        
        # Set check out time and location
        attendance.check_out = timezone.now()
        attendance.check_out_location = {
            'latitude': user_lat,
            'longitude': user_lon,
            'timestamp': timezone.now().isoformat()
        }
        attendance.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully checked out at {attendance.check_out.strftime("%H:%M")}',
            'checkOutTime': attendance.check_out.strftime('%H:%M'),
            'hoursWorked': str(attendance.hours_worked or 0)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# Missing view classes for attendance management
class AttendanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/attendance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add attendance dashboard logic here
        return context


class ClockInOutView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/attendance/clock_inout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add clock in/out logic here
        return context


class UserAttendanceView(LoginRequiredMixin, ListView):
    template_name = 'hrms/attendance/user_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 20
    
    def get_queryset(self):
        # Return user's attendance records
        return []  # Placeholder
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user attendance logic here
        return context


class AttendanceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'hrms/attendance/list.html'
    context_object_name = 'attendances'
    paginate_by = 50
    
    def get_queryset(self):
        # Return all attendance records for admin
        return []  # Placeholder
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add attendance list logic here
        return context


# =============================================================================
# HAWWA INTEGRATION VIEWS
# =============================================================================

class VendorStaffListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all vendor staff assignments"""
    model = VendorStaff
    template_name = 'hrms/vendor_integration/staff_list.html'
    context_object_name = 'vendor_staff'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = VendorStaff.objects.select_related(
            'employee__user', 'vendor_profile', 'created_by'
        ).order_by('-created_at')
        
        # Filter by vendor if specified
        vendor_id = self.request.GET.get('vendor')
        if vendor_id:
            queryset = queryset.filter(vendor_profile_id=vendor_id)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(assignment_status=status)
            
        # Filter by role
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(vendor_role=role)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from vendors.models import VendorProfile
        context['vendors'] = VendorProfile.objects.filter(status='active')
        context['status_choices'] = VendorStaff.ASSIGNMENT_STATUS_CHOICES
        context['role_choices'] = VendorStaff.VENDOR_ROLE_CHOICES
        context['selected_vendor'] = self.request.GET.get('vendor', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_role'] = self.request.GET.get('role', '')
        return context


class VendorStaffCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create new vendor staff assignment"""
    model = VendorStaff
    template_name = 'hrms/vendor_integration/staff_create.html'
    fields = [
        'employee', 'vendor_profile', 'vendor_role', 'assignment_status',
        'start_date', 'end_date', 'specializations', 'service_areas',
        'available_days', 'available_hours', 'certifications',
        'work_permit_number', 'work_permit_expiry', 'visa_status', 'visa_expiry'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('hrms:vendor_staff_list')


class VendorStaffDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View vendor staff assignment details"""
    model = VendorStaff
    template_name = 'hrms/vendor_integration/staff_detail.html'
    context_object_name = 'vendor_staff'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_assignments'] = self.object.service_assignments.all()[:10]
        context['training_records'] = self.object.training_records.all()[:10]
        context['recent_assignments_count'] = self.object.service_assignments.filter(
            assigned_date__gte=timezone.now() - timedelta(days=30)
        ).count()
        return context


class ServiceAssignmentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list service assignments"""
    model = ServiceAssignment
    template_name = 'hrms/vendor_integration/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 25
    
    def get_queryset(self):
        return ServiceAssignment.objects.select_related(
            'vendor_staff__employee__user', 'vendor_staff__vendor_profile',
            'booking', 'assigned_by'
        ).order_by('-assigned_date')


class VendorIntegrationDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Dashboard for vendor integration analytics"""
    template_name = 'hrms/vendor_integration/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Staff statistics
        context['total_vendor_staff'] = VendorStaff.objects.count()
        context['active_staff'] = VendorStaff.objects.filter(assignment_status='active').count()
        context['staff_by_role'] = dict(
            VendorStaff.objects.values_list('vendor_role').annotate(Count('id'))
        )
        
        # Service assignment statistics
        context['total_assignments'] = ServiceAssignment.objects.count()
        context['active_assignments'] = ServiceAssignment.objects.filter(
            assignment_status__in=['assigned', 'accepted', 'in_progress']
        ).count()
        context['completed_assignments'] = ServiceAssignment.objects.filter(
            assignment_status='completed'
        ).count()
        
        # Recent activity
        context['recent_assignments'] = ServiceAssignment.objects.select_related(
            'vendor_staff__employee__user', 'booking'
        ).order_by('-assigned_date')[:5]
        
        # Performance metrics
        from django.db import models
        context['avg_rating'] = ServiceAssignment.objects.filter(
            customer_rating__isnull=False
        ).aggregate(avg_rating=models.Avg('customer_rating'))['avg_rating'] or 0
        
        return context


