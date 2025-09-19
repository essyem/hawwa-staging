from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Company, Department, Position, Grade, EmployeeProfile,
    LeaveType, LeaveBalance, LeaveApplication, 
    TrainingCategory, TrainingProgram, TrainingSession, TrainingEnrollment,
    PerformanceCycle, PerformanceReview,
    PayrollPeriod, PayrollItem
)


# ============================================================================
# USER & AUTH SERIALIZERS
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'full_name', 'is_active']


# ============================================================================
# ORGANIZATIONAL SERIALIZERS
# ============================================================================

class CompanySerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = '__all__'
    
    def get_employee_count(self, obj):
        return sum(dept.employees.count() for dept in obj.departments.all())


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.user.get_full_name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = '__all__'
    
    def get_employee_count(self, obj):
        return obj.employees.count()


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = '__all__'
    
    def get_employee_count(self, obj):
        return obj.employees.count()


class GradeSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = '__all__'
    
    def get_employee_count(self, obj):
        return obj.employees.count()


# ============================================================================
# EMPLOYEE SERIALIZERS
# ============================================================================

class EmployeeProfileListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    total_salary = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    years_of_service = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'employee_id', 'user', 'department_name', 'position_title',
            'employment_type', 'hire_date', 'status', 'total_salary', 'age', 'years_of_service'
        ]
    
    def get_total_salary(self, obj):
        return (obj.basic_salary or 0) + (obj.housing_allowance or 0) + \
               (obj.transport_allowance or 0) + (obj.other_allowances or 0)
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from django.utils import timezone
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - \
                   ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None
    
    def get_years_of_service(self, obj):
        if obj.hire_date:
            from django.utils import timezone
            today = timezone.now().date()
            return today.year - obj.hire_date.year - \
                   ((today.month, today.day) < (obj.hire_date.month, obj.hire_date.day))
        return None


class EmployeeProfileDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    grade = GradeSerializer(read_only=True)
    manager_name = serializers.CharField(source='manager.user.get_full_name', read_only=True)
    total_salary = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    years_of_service = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeProfile
        fields = '__all__'
    
    def get_total_salary(self, obj):
        return (obj.basic_salary or 0) + (obj.housing_allowance or 0) + \
               (obj.transport_allowance or 0) + (obj.other_allowances or 0)
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from django.utils import timezone
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - \
                   ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None
    
    def get_years_of_service(self, obj):
        if obj.hire_date:
            from django.utils import timezone
            today = timezone.now().date()
            return today.year - obj.hire_date.year - \
                   ((today.month, today.day) < (obj.hire_date.month, obj.hire_date.day))
        return None


# ============================================================================
# LEAVE SERIALIZERS
# ============================================================================

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    remaining_days = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveBalance
        fields = '__all__'
    
    def get_remaining_days(self, obj):
        return obj.entitled_days - obj.used_days - obj.pending_days


class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ['applied_date', 'approved_by', 'approved_date']


# ============================================================================
# TRAINING SERIALIZERS
# ============================================================================

class TrainingCategorySerializer(serializers.ModelSerializer):
    program_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingCategory
        fields = '__all__'
    
    def get_program_count(self, obj):
        return obj.programs.count()


class TrainingProgramSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.get_full_name', read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingProgram
        fields = '__all__'
    
    def get_enrollment_count(self, obj):
        return obj.enrollments.count()
    
    def get_completion_rate(self, obj):
        total_enrollments = obj.enrollments.count()
        if total_enrollments == 0:
            return 0
        completed_enrollments = obj.enrollments.filter(status='completed').count()
        return round((completed_enrollments / total_enrollments) * 100, 2)


class TrainingSessionSerializer(serializers.ModelSerializer):
    program_title = serializers.CharField(source='program.title', read_only=True)
    attendee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingSession
        fields = '__all__'
    
    def get_attendee_count(self, obj):
        return obj.attendees.count()


class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    program_title = serializers.CharField(source='program.title', read_only=True)
    
    class Meta:
        model = TrainingEnrollment
        fields = '__all__'


# ============================================================================
# PERFORMANCE SERIALIZERS
# ============================================================================

class PerformanceCycleSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceCycle
        fields = '__all__'
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)
    
    class Meta:
        model = PerformanceReview
        fields = '__all__'


# ============================================================================
# PAYROLL SERIALIZERS
# ============================================================================

class PayrollPeriodSerializer(serializers.ModelSerializer):
    payroll_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PayrollPeriod
        fields = '__all__'
    
    def get_payroll_count(self, obj):
        return obj.payroll_items.count()
    
    def get_total_amount(self, obj):
        from django.db.models import Sum
        return obj.payroll_items.aggregate(total=Sum('net_salary'))['total'] or 0


class PayrollItemSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    period_name = serializers.CharField(source='payroll_period.name', read_only=True)
    
    class Meta:
        model = PayrollItem
        fields = '__all__'
        read_only_fields = ['gross_salary', 'total_deductions', 'net_salary']


# ============================================================================
# DASHBOARD SERIALIZERS
# ============================================================================

class DashboardStatsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    pending_leaves = serializers.IntegerField()
    active_training_programs = serializers.IntegerField()
    this_month_hires = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=10, decimal_places=2)


class RecentActivitySerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField()
    user = serializers.CharField()
    url = serializers.CharField(required=False)
