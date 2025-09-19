from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic.edit import UpdateView
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import (
    Company, Department, Position, Grade, EmployeeProfile,
    LeaveType, LeaveBalance, LeaveApplication, LeaveApproval,
    TrainingCategory, TrainingProgram, TrainingSession, TrainingEnrollment,
    EducationLevel, DocumentType, EmployeeEducation, EmployeeDocument,
    PerformanceCycle, PerformanceReview,
    PayrollPeriod, PayrollItem, ReportTemplate, ScheduledReport, ReportExecution,
    WorkSchedule, EmployeeSchedule, Attendance, AttendanceSession, AttendanceRequest, TimeSheet, AttendanceSettings,
    VendorStaff, ServiceAssignment, VendorStaffTraining
)
from django.contrib import messages

# Currency formatting utilities for admin
def format_currency_admin(value):
    """Format currency values for admin display"""
    if value is None or value == '':
        return format_html('<span style="color: #999;">QAR 0.00</span>')
    
    try:
        amount = float(value)
        formatted = f"{amount:,.2f}"
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">QAR {}</span>', 
            formatted
        )
    except (ValueError, TypeError):
        return format_html('<span style="color: #999;">QAR 0.00</span>')

def format_currency_short_admin(value):
    """Format currency values for admin display without decimals"""
    if value is None or value == '':
        return format_html('<span style="color: #999;">QAR 0</span>')
    
    try:
        amount = float(value)
        formatted = f"{amount:,.0f}"
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">QAR {}</span>', 
            formatted
        )
    except (ValueError, TypeError):
        return format_html('<span style="color: #999;">QAR 0</span>')

# =============================================================================
# ORGANIZATIONAL MANAGEMENT ADMIN
# =============================================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'legal_name', 'country', 'phone', 'email', 'established_date']
    list_filter = ['country', 'established_date']
    search_fields = ['name', 'legal_name', 'registration_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'legal_name', 'registration_number', 'tax_number')
        }),
        ('Contact Information', {
            'fields': ('address', 'country', 'phone', 'email', 'website')
        }),
        ('Additional Information', {
            'fields': ('logo', 'established_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_count(self, obj):
        return obj.departments.aggregate(
            total=Count('employees')
        )['total'] or 0
    employee_count.short_description = 'Total Employees'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'head', 'employee_count', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['head']
    
    def employee_count(self, obj):
        return obj.employees.filter(status='active').count()
    employee_count.short_description = 'Active Employees'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent', 'head')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'level', 'min_salary_display', 'max_salary_display']
    list_filter = ['department', 'level', 'is_active']
    search_fields = ['title', 'code']
    
    def min_salary_display(self, obj):
        return format_currency_admin(obj.min_salary)
    min_salary_display.short_description = 'Min Salary'
    min_salary_display.admin_order_field = 'min_salary'
    
    def max_salary_display(self, obj):
        return format_currency_admin(obj.max_salary)
    max_salary_display.short_description = 'Max Salary'
    max_salary_display.admin_order_field = 'max_salary'

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'min_salary_display', 'max_salary_display', 'annual_increment_percentage']
    search_fields = ['name', 'code']
    
    def min_salary_display(self, obj):
        return format_currency_admin(obj.min_salary)
    min_salary_display.short_description = 'Min Salary'
    min_salary_display.admin_order_field = 'min_salary'
    
    def max_salary_display(self, obj):
        return format_currency_admin(obj.max_salary)
    max_salary_display.short_description = 'Max Salary'
    max_salary_display.admin_order_field = 'max_salary'


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level_order', 'is_active']
    list_filter = ['is_active', 'code']
    search_fields = ['name']
    ordering = ['level_order', 'name']


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_required', 'has_expiry', 'is_active']
    list_filter = ['category', 'is_required', 'has_expiry', 'is_active']
    search_fields = ['name']
    ordering = ['category', 'name']


class EmployeeEducationInline(admin.TabularInline):
    model = EmployeeEducation
    extra = 0
    fields = ['education_level', 'institution_name', 'field_of_study', 'start_month', 'start_year', 'end_month', 'end_year', 'is_current', 'is_verified']
    readonly_fields = ['is_verified']


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    fields = ['document_type', 'title', 'document_number', 'file', 'issue_date', 'expiry_date', 'is_verified']
    readonly_fields = ['is_verified', 'file_size']

# =============================================================================
# PERSONNEL ADMINISTRATION ADMIN
# =============================================================================

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'full_name', 'department', 'position', 
        'employment_type', 'hire_date', 'status', 'salary_display'
    ]
    list_filter = [
        'status', 'employment_type', 'department', 'position', 
        'gender', 'marital_status', 'hire_date'
    ]
    search_fields = [
        'employee_id', 'user__first_name', 'user__last_name', 
        'user__email', 'personal_email', 'phone_number', 'qatar_id', 'passport_number'
    ]
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'age', 'years_of_service']
    date_hierarchy = 'hire_date'
    inlines = [EmployeeEducationInline, EmployeeDocumentInline]
    
    fieldsets = (
        ('User Account', {
            'fields': ('user', 'employee_id', 'status')
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'place_of_birth', 'nationality', 'gender', 
                'marital_status', 'blood_group', 'photo'
            )
        }),
        ('Identity Documents', {
            'fields': (
                'qatar_id', 'qatar_id_expiry', 'passport_number', 'passport_expiry', 
                'passport_issue_country', 'national_id'
            )
        }),
        ('Contact Information', {
            'fields': (
                'personal_email', 'phone_number', 'current_address', 'permanent_address'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone', 
                'emergency_contact_relationship'
            )
        }),
        ('Employment Information', {
            'fields': (
                'department', 'position', 'grade', 'employment_type', 
                'work_location', 'hire_date', 'termination_date'
            )
        }),
        ('Salary Information', {
            'fields': (
                'basic_salary', 'housing_allowance', 'transport_allowance', 
                'other_allowances'
            )
        }),
        ('Calculated Fields', {
            'fields': ('age', 'years_of_service'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'user__first_name'
    
    def salary_display(self, obj):
        total = (obj.basic_salary or 0) + (obj.housing_allowance or 0) + \
                (obj.transport_allowance or 0) + (obj.other_allowances or 0)
        return format_currency_admin(total)
    salary_display.short_description = 'Total Salary'
    
    def age(self, obj):
        if obj.date_of_birth:
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - \
                   ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return '-'
    age.short_description = 'Age'
    
    def years_of_service(self, obj):
        if obj.hire_date:
            today = timezone.now().date()
            return today.year - obj.hire_date.year - \
                   ((today.month, today.day) < (obj.hire_date.month, obj.hire_date.day))
        return '-'
    years_of_service.short_description = 'Years of Service'
    
    actions = ['activate_employees', 'deactivate_employees']
    
    def activate_employees(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} employees activated.')
    activate_employees.short_description = 'Activate selected employees'
    
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} employees deactivated.')
    deactivate_employees.short_description = 'Deactivate selected employees'


@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'education_level', 'institution_name', 'field_of_study', 'duration_display', 'is_completed', 'is_verified']
    list_filter = ['education_level', 'is_completed', 'is_verified', 'country', 'start_year']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name', 'institution_name', 'field_of_study']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'education_level', 'institution_name', 'field_of_study', 'degree_title')
        }),
        ('Duration', {
            'fields': ('start_month', 'start_year', 'end_month', 'end_year', 'is_current', 'is_completed')
        }),
        ('Additional Information', {
            'fields': ('grade_gpa', 'country')
        }),
        ('Documents', {
            'fields': ('certificate', 'transcript')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['verify_selected', 'unverify_selected']
    
    def verify_selected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verified_date=timezone.now()
        )
        self.message_user(request, f'{updated} education records verified.')
    verify_selected.short_description = 'Verify selected education records'
    
    def unverify_selected(self, request, queryset):
        updated = queryset.update(
            is_verified=False,
            verified_by=None,
            verified_date=None
        )
        self.message_user(request, f'{updated} education records unverified.')
    unverify_selected.short_description = 'Unverify selected education records'


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'title', 'document_number', 'issue_date', 'expiry_date', 'is_verified', 'is_expired']
    list_filter = ['document_type', 'is_verified', 'is_active', 'expiry_date']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name', 'title', 'document_number']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'is_expired', 'expires_soon']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'document_type', 'title', 'document_number')
        }),
        ('File Information', {
            'fields': ('file', 'file_size')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date', 'is_expired', 'expires_soon')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'verified_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['verify_selected', 'unverify_selected', 'mark_active', 'mark_inactive']
    
    def verify_selected(self, request, queryset):
        updated = queryset.update(is_verified=True, verified_by=request.user)
        self.message_user(request, f'{updated} documents verified.')
    verify_selected.short_description = 'Verify selected documents'
    
    def unverify_selected(self, request, queryset):
        updated = queryset.update(is_verified=False, verified_by=None)
        self.message_user(request, f'{updated} documents unverified.')
    unverify_selected.short_description = 'Unverify selected documents'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} documents marked as active.')
    mark_active.short_description = 'Mark as active'
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} documents marked as inactive.')
    mark_inactive.short_description = 'Mark as inactive'
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

# =============================================================================
# LEAVE MANAGEMENT ADMIN
# =============================================================================

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'days_allowed_per_year', 'is_paid', 'is_active']
    list_filter = ['is_paid', 'requires_approval', 'is_active']
    search_fields = ['name', 'code']

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'entitled_days', 'used_days', 'available_days']
    list_filter = ['leave_type', 'year']
    search_fields = ['employee__employee_id', 'employee__user__username']

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status', 'substitute_employee']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__employee_id', 'employee__user__username']
    date_hierarchy = 'start_date'
    readonly_fields = ['applied_on']
    
    fieldsets = (
        ('Leave Details', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'reason')
        }),
        ('Substitution', {
            'fields': ('substitute_employee', 'substitute_notes'),
            'classes': ('collapse',)
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_on', 'comments', 'applied_on')
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'substitute_pending', 'manager_pending', 'hr_pending']).update(
            status='approved',
            approved_by=request.user,
            approved_on=timezone.now()
        )
        self.message_user(request, f"Approved {updated} leave applications.")
    approve_selected.short_description = "Approve selected applications"
    
    def reject_selected(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'substitute_pending', 'manager_pending', 'hr_pending']).update(
            status='rejected',
            approved_by=request.user,
            approved_on=timezone.now()
        )
        self.message_user(request, f"Rejected {updated} leave applications.")
    reject_selected.short_description = "Reject selected applications"


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):
    list_display = ['leave_application', 'approver', 'approval_type', 'status', 'approved_on']
    list_filter = ['approval_type', 'status', 'approved_on']
    search_fields = ['leave_application__employee__employee_id', 'approver__username']
    date_hierarchy = 'approved_on'
    readonly_fields = ['created_on']
    
    fieldsets = (
        ('Approval Details', {
            'fields': ('leave_application', 'approver', 'approval_type', 'status')
        }),
        ('Comments & Dates', {
            'fields': ('comments', 'approved_on', 'created_on')
        }),
    )

# =============================================================================
# TRAINING ADMIN
# =============================================================================

@admin.register(TrainingCategory)
class TrainingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'category', 'training_type', 'level', 'duration_hours']
    list_filter = ['category', 'training_type', 'level', 'is_mandatory', 'is_active']
    search_fields = ['title', 'code']

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['program', 'trainer_name', 'start_date', 'end_date', 'location', 'status']
    list_filter = ['status', 'program__category', 'start_date']
    search_fields = ['program__title', 'trainer_name']

@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'session', 'attendance_status', 'completion_status', 'score']
    list_filter = ['attendance_status', 'completion_status', 'session__program__category']
    search_fields = ['employee__employee_id', 'employee__user__username']

# =============================================================================
# PERFORMANCE MANAGEMENT ADMIN
# =============================================================================

@admin.register(PerformanceCycle)
class PerformanceCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'review_due_date', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['name']

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'overall_rating', 'status', 'final_review_date']
    list_filter = ['status', 'cycle', 'overall_rating']
    search_fields = ['employee__employee_id', 'employee__user__username']

# =============================================================================
# TIME & ATTENDANCE ADMIN
# =============================================================================

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'schedule_type', 'start_time', 'end_time', 'daily_hours', 'weekly_hours', 'is_active']
    list_filter = ['schedule_type', 'is_active', 'require_location']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'schedule_type', 'description', 'is_active')
        }),
        ('Working Hours', {
            'fields': ('start_time', 'end_time', 'break_duration', 'work_days', 'weekly_hours')
        }),
        ('Overtime Settings', {
            'fields': ('overtime_after_hours', 'overtime_rate')
        }),
        ('Grace Periods', {
            'fields': ('late_grace_minutes', 'early_departure_minutes')
        }),
        ('Location Settings', {
            'fields': ('require_location', 'allowed_locations', 'location_radius'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def daily_hours(self, obj):
        return f"{obj.daily_hours:.2f}h"
    daily_hours.short_description = 'Daily Hours'

@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display = ['employee', 'schedule', 'effective_from', 'effective_to', 'allow_remote_work', 'require_photo_verification']
    list_filter = ['schedule', 'allow_remote_work', 'require_photo_verification', 'effective_from']
    search_fields = ['employee__employee_id', 'employee__user__username', 'schedule__name']
    date_hierarchy = 'effective_from'
    raw_id_fields = ['employee']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('employee', 'schedule')
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Custom Overrides', {
            'fields': ('custom_start_time', 'custom_end_time', 'custom_work_days'),
            'classes': ('collapse',)
        }),
        ('Special Settings', {
            'fields': ('require_photo_verification', 'allow_remote_work')
        }),
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in', 'check_out', 'duration_display', 'overtime_hours', 'is_verified']
    list_filter = ['status', 'is_verified', 'is_remote', 'requires_approval', 'date']
    search_fields = ['employee__employee_id', 'employee__user__username']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'duration_display', 'check_in_delay']
    raw_id_fields = ['employee', 'verified_by', 'approved_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('check_in', 'check_out', 'break_start', 'break_end', 'total_break_time')
        }),
        ('Hours Calculation', {
            'fields': ('scheduled_hours', 'hours_worked', 'overtime_hours', 'duration_display', 'check_in_delay'),
            'classes': ('collapse',)
        }),
        ('Location & Device', {
            'fields': ('check_in_location', 'check_out_location', 'is_remote', 'check_in_ip', 'check_out_ip', 'device_info'),
            'classes': ('collapse',)
        }),
        ('Photo Verification', {
            'fields': ('check_in_photo', 'check_out_photo'),
            'classes': ('collapse',)
        }),
        ('Verification & Approval', {
            'fields': ('is_verified', 'verified_by', 'requires_approval', 'approved_by', 'approved_at')
        }),
        ('Notes', {
            'fields': ('notes', 'manager_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_verified', 'mark_approved', 'calculate_hours']
    
    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True, verified_by=request.user)
        self.message_user(request, f'{updated} attendance records marked as verified.')
    mark_verified.short_description = "Mark selected attendance as verified"
    
    def mark_approved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            requires_approval=False, 
            approved_by=request.user, 
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} attendance records approved.')
    mark_approved.short_description = "Approve selected attendance records"
    
    def calculate_hours(self, request, queryset):
        updated = 0
        for attendance in queryset:
            if attendance.check_in and attendance.check_out:
                attendance.calculate_hours_worked()
                attendance.save()
                updated += 1
        self.message_user(request, f'Hours recalculated for {updated} attendance records.')
    calculate_hours.short_description = "Recalculate hours for selected records"


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance', 'session_type', 'check_in', 'check_out', 'duration_display', 'reason', 'is_verified']
    list_filter = ['session_type', 'is_verified', 'check_in']
    search_fields = ['employee__employee_id', 'employee__user__username', 'reason']
    date_hierarchy = 'check_in'
    readonly_fields = ['created_at', 'updated_at', 'duration_display']
    raw_id_fields = ['attendance', 'employee', 'verified_by']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('attendance', 'employee', 'session_type', 'reason')
        }),
        ('Time Tracking', {
            'fields': ('check_in', 'check_out', 'duration_display')
        }),
        ('Location & Device', {
            'fields': ('check_in_location', 'check_out_location', 'check_in_ip', 'check_out_ip', 'device_info'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_verified', 'close_session']
    
    def duration_display(self, obj):
        """Display session duration in a readable format"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "Ongoing"
    duration_display.short_description = "Duration"
    
    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True, verified_by=request.user)
        self.message_user(request, f'{updated} attendance sessions marked as verified.')
    mark_verified.short_description = "Mark selected sessions as verified"
    
    def close_session(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for session in queryset.filter(check_out__isnull=True):
            session.check_out = timezone.now()
            session.save()
            updated += 1
        self.message_user(request, f'{updated} ongoing sessions were closed.')
    close_session.short_description = "Close ongoing sessions"


@admin.register(AttendanceRequest)
class AttendanceRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'request_type', 'requested_date', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['request_type', 'status', 'submitted_at']
    search_fields = ['employee__employee_id', 'employee__user__username', 'reason']
    date_hierarchy = 'submitted_at'
    readonly_fields = ['submitted_at', 'created_at', 'updated_at']
    raw_id_fields = ['employee', 'attendance', 'reviewed_by']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('employee', 'request_type', 'attendance')
        }),
        ('Request Details', {
            'fields': ('requested_date', 'requested_check_in', 'requested_check_out', 'reason')
        }),
        ('Supporting Documents', {
            'fields': ('supporting_document',)
        }),
        ('Review & Approval', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_comments')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests approved.')
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests rejected.')
    reject_requests.short_description = "Reject selected requests"

@admin.register(TimeSheet)
class TimeSheetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'start_date', 'end_date', 'total_worked_hours', 'total_overtime_hours', 'status', 'created_at']
    list_filter = ['status', 'period_type', 'start_date', 'created_at']
    search_fields = ['employee__user__username', 'employee__user__first_name', 'employee__user__last_name']
    readonly_fields = ['total_scheduled_hours', 'total_worked_hours', 'total_overtime_hours', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'period_type', 'start_date', 'end_date')
        }),
        ('Summary', {
            'fields': ('total_scheduled_hours', 'total_worked_hours', 'total_overtime_hours', 'total_break_hours')
        }),
        ('Status & Approval', {
            'fields': ('status', 'submitted_at', 'approved_by', 'approved_at')
        }),
        ('Comments', {
            'fields': ('employee_comments', 'manager_comments')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ['office_name', 'latitude', 'longitude', 'radius', 'is_active']
    list_filter = ['is_active']
    search_fields = ['office_name']
    
    fieldsets = (
        ('Office Location', {
            'fields': ('office_name', 'latitude', 'longitude', 'radius', 'is_active'),
            'description': 'Configure office locations for attendance tracking'
        }),
        ('Attendance Rules', {
            'fields': ('allow_early_checkin', 'early_checkin_minutes', 'allow_late_checkout', 'late_checkout_minutes'),
            'description': 'Set rules for check-in and check-out timing'
        }),
        ('Additional Settings', {
            'fields': ('require_photo', 'auto_deduct_break', 'default_break_minutes'),
            'description': 'Configure photo verification and break settings'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('office_name')


# ============================================================================
# HAWWA INTEGRATION ADMIN CLASSES
# ============================================================================

@admin.register(VendorStaff)
class VendorStaffAdmin(admin.ModelAdmin):
    list_display = (
        'employee_name', 'vendor_business_name', 'vendor_role', 
        'assignment_status', 'service_rating', 'completed_assignments', 
        'start_date', 'is_active'
    )
    list_filter = (
        'assignment_status', 'vendor_role', 'start_date', 
        'vendor_profile__business_type'
    )
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name',
        'employee__employee_id', 'vendor_profile__business_name'
    )
    raw_id_fields = ('employee', 'vendor_profile', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'is_active')
    
    fieldsets = (
        ('Staff Assignment', {
            'fields': ('employee', 'vendor_profile', 'vendor_role', 'assignment_status')
        }),
        ('Assignment Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Skills & Availability', {
            'fields': ('specializations', 'service_areas', 'available_days', 'available_hours'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('service_rating', 'completed_assignments', 'total_service_hours'),
            'classes': ('collapse',)
        }),
        ('Certifications & Training', {
            'fields': ('certifications', 'training_completed'),
            'classes': ('collapse',)
        }),
        ('Qatar Compliance', {
            'fields': ('work_permit_number', 'work_permit_expiry', 'visa_status', 'visa_expiry'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.user.get_full_name()
    employee_name.short_description = 'Employee Name'
    
    def vendor_business_name(self, obj):
        return obj.vendor_profile.business_name
    vendor_business_name.short_description = 'Vendor Business'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee__user', 'vendor_profile', 'created_by'
        )


@admin.register(ServiceAssignment)
class ServiceAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'staff_name', 'booking_id', 'assignment_status', 
        'assigned_date', 'estimated_hours', 'actual_hours',
        'customer_rating'
    )
    list_filter = (
        'assignment_status', 'assigned_date', 'customer_rating',
        'vendor_staff__vendor_role'
    )
    search_fields = (
        'vendor_staff__employee__user__first_name',
        'vendor_staff__employee__user__last_name',
        'booking__id', 'booking__customer__first_name'
    )
    raw_id_fields = ('vendor_staff', 'booking', 'assigned_by')
    readonly_fields = ('assigned_date', 'created_at', 'updated_at', 'duration_hours')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('vendor_staff', 'booking', 'assignment_status', 'assigned_by')
        }),
        ('Timeline', {
            'fields': ('assigned_date', 'accepted_date', 'start_date', 'completion_date')
        }),
        ('Service Information', {
            'fields': ('service_notes', 'special_instructions', 'estimated_hours', 'actual_hours', 'duration_hours')
        }),
        ('Quality & Feedback', {
            'fields': ('customer_rating', 'customer_feedback', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def staff_name(self, obj):
        return obj.vendor_staff.employee.user.get_full_name()
    staff_name.short_description = 'Staff Name'
    
    def booking_id(self, obj):
        return f"#{obj.booking.id}"
    booking_id.short_description = 'Booking'


@admin.register(VendorStaffTraining)
class VendorStaffTrainingAdmin(admin.ModelAdmin):
    list_display = (
        'staff_name', 'training_title', 'status', 
        'enrollment_date', 'completion_date', 'score'
    )
    list_filter = (
        'status', 'enrollment_date', 'completion_date',
        'training_program__category'
    )
    search_fields = (
        'vendor_staff__employee__user__first_name',
        'vendor_staff__employee__user__last_name',
        'training_program__title'
    )
    raw_id_fields = ('vendor_staff', 'training_program')
    readonly_fields = ('enrollment_date', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Training Assignment', {
            'fields': ('vendor_staff', 'training_program', 'status')
        }),
        ('Timeline', {
            'fields': ('enrollment_date', 'start_date', 'completion_date')
        }),
        ('Performance', {
            'fields': ('score', 'certificate_number', 'certificate_expiry')
        }),
        ('Feedback', {
            'fields': ('trainer_notes', 'participant_feedback'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def staff_name(self, obj):
        return obj.vendor_staff.employee.user.get_full_name()
    staff_name.short_description = 'Staff Name'
    
    def training_title(self, obj):
        return obj.training_program.title
    training_title.short_description = 'Training Program'


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "HRMS Administration"
admin.site.site_title = "HRMS Admin Portal"
admin.site.index_title = "Welcome to HRMS Administration"