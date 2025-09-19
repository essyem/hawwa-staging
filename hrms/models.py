from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

User = get_user_model()

# =============================================================================
# 1. ORGANIZATIONAL MANAGEMENT MODELS
# =============================================================================

class Company(models.Model):
    """Company information"""
    name = models.CharField(max_length=200, unique=True)
    legal_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, unique=True)
    tax_number = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    country = models.CharField(max_length=100, default='Qatar')
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company/', blank=True)
    established_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

class Department(models.Model):
    """Department/Division structure"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subdepartments')
    head = models.ForeignKey('EmployeeProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'parent']

    def __str__(self):
        return f"{self.code} - {self.name}"

class Position(models.Model):
    """Job positions/roles"""
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    level = models.CharField(max_length=20, choices=[
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive')
    ])
    min_salary = models.DecimalField(max_digits=10, decimal_places=2)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2)
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.title}"

class Grade(models.Model):
    """Employee grades/bands"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2)
    annual_increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    benefits_package = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class EducationLevel(models.Model):
    """Education levels for employee qualifications"""
    EDUCATION_CHOICES = [
        ('high_school', 'High School'),
        ('higher_secondary', 'Higher Secondary'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('professional', 'Professional Certification'),
        ('vocational', 'Vocational Training'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, choices=EDUCATION_CHOICES, unique=True)
    level_order = models.PositiveIntegerField(default=1, help_text="Order level (1=lowest, 10=highest)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level_order', 'name']
    
    def __str__(self):
        return self.name


class DocumentType(models.Model):
    """Types of documents that can be uploaded for employees"""
    DOCUMENT_CATEGORIES = [
        ('identity', 'Identity Documents'),
        ('education', 'Educational Documents'),
        ('employment', 'Employment Documents'),
        ('medical', 'Medical Documents'),
        ('visa', 'Visa & Immigration'),
        ('other', 'Other Documents'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=DOCUMENT_CATEGORIES)
    is_required = models.BooleanField(default=False)
    has_expiry = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

# =============================================================================
# 2. PERSONNEL ADMINISTRATION MODELS
# =============================================================================

class EmployeeProfile(models.Model):
    """Extended employee profile"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=20, unique=True, default='EMP001')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, default='Unknown')
    nationality = models.CharField(max_length=100, default='Qatari')
    
    # Qatar ID Information
    qatar_id = models.CharField(max_length=20, blank=True, verbose_name='Qatar ID Number')
    qatar_id_expiry = models.DateField(null=True, blank=True, verbose_name='Qatar ID Expiry Date')
    
    # Passport Information
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True, verbose_name='Passport Expiry Date')
    passport_issue_country = models.CharField(max_length=100, blank=True, default='Qatar')
    
    # Other ID
    national_id = models.CharField(max_length=50, blank=True, verbose_name='National ID (if different from Qatar ID)')
    
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], default='male')
    marital_status = models.CharField(max_length=20, choices=[
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], default='single')
    blood_group = models.CharField(max_length=5, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], blank=True)
    
    # Contact Information
    personal_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, default='00000000')
    emergency_contact_name = models.CharField(max_length=100, default='Unknown')
    emergency_contact_phone = models.CharField(max_length=30, default='00000000')
    emergency_contact_relationship = models.CharField(max_length=50, default='Unknown')
    current_address = models.TextField(default='Unknown')
    permanent_address = models.TextField(default='Unknown')
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees', null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='employees', null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='employees', null=True, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    employment_type = models.CharField(max_length=20, choices=[
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('intern', 'Intern'),
        ('consultant', 'Consultant')
    ], default='permanent')
    work_location = models.CharField(max_length=100, default='Doha')
    hire_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('probation', 'Probation'),
        ('notice_period', 'Notice Period'),
        ('terminated', 'Terminated'),
        ('resigned', 'Resigned')
    ], default='active')
    
    # Files
    photo = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    resume = models.FileField(upload_to='employees/resumes/', blank=True, null=True)
    contract = models.FileField(upload_to='employees/contracts/', blank=True, null=True)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_employees', null=True, blank=True)

    @property
    def total_salary(self):
        return self.basic_salary + self.housing_allowance + self.transport_allowance + self.other_allowances

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"


class EmployeeEducation(models.Model):
    """Employee education records"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='educations')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.PROTECT)
    institution_name = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    degree_title = models.CharField(max_length=200, blank=True)
    
    # Date Information
    start_month = models.PositiveIntegerField(
        choices=[(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        verbose_name='Start Month'
    )
    start_year = models.PositiveIntegerField(verbose_name='Start Year')
    end_month = models.PositiveIntegerField(
        choices=[(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        null=True, blank=True,
        verbose_name='End Month'
    )
    end_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='End Year')
    
    # Status
    is_completed = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False, verbose_name='Currently Studying')
    grade_gpa = models.CharField(max_length=50, blank=True, verbose_name='Grade/GPA')
    country = models.CharField(max_length=100, default='Qatar')
    
    # Documents
    certificate = models.FileField(upload_to='employees/education/', blank=True, null=True)
    transcript = models.FileField(upload_to='employees/education/', blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_educations')
    verified_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-end_year', '-start_year', 'education_level__level_order']
        verbose_name = 'Employee Education'
        verbose_name_plural = 'Employee Education Records'
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.education_level.name} from {self.institution_name}"
    
    @property
    def duration_display(self):
        start = f"{self.get_start_month_display()} {self.start_year}"
        if self.is_current:
            return f"{start} - Present"
        elif self.end_month and self.end_year:
            end = f"{self.get_end_month_display()} {self.end_year}"
            return f"{start} - {end}"
        return start


class EmployeeDocument(models.Model):
    """Employee document management"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    document_number = models.CharField(max_length=100, blank=True)
    
    # File
    file = models.FileField(upload_to='employees/documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Dates
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='hrms_uploaded_documents')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='hrms_verified_documents')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Document'
        verbose_name_plural = 'Employee Documents'
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.title}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def expires_soon(self):
        if self.expiry_date:
            from django.utils import timezone
            from datetime import timedelta
            warning_date = timezone.now().date() + timedelta(days=30)
            return self.expiry_date <= warning_date
        return False
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

# =============================================================================
# 3. LEAVE MANAGEMENT MODELS
# =============================================================================

class LeaveType(models.Model):
    """Types of leave"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    days_allowed_per_year = models.IntegerField()
    carry_forward_days = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_consecutive_days = models.IntegerField(null=True, blank=True)
    notice_days_required = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class LeaveBalance(models.Model):
    """Employee leave balances"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField()
    entitled_days = models.DecimalField(max_digits=5, decimal_places=2)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    @property
    def available_days(self):
        return self.entitled_days - self.used_days - self.pending_days

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.code} ({self.year})"

class LeaveApplication(models.Model):
    """Leave applications"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    
    # Substitution field - who will cover the work
    substitute_employee = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='substitute_leaves',
        help_text="Employee who will cover responsibilities during leave"
    )
    substitute_notes = models.TextField(
        blank=True,
        help_text="Notes about work handover and responsibilities"
    )
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('substitute_pending', 'Substitute Approval Pending'),
        ('manager_pending', 'Manager Approval Pending'), 
        ('hr_pending', 'HR Approval Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_on = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.code} ({self.start_date} to {self.end_date})"
    
    def get_next_approver(self):
        """Get the next person who needs to approve this leave"""
        if self.status == 'pending' and self.substitute_employee:
            # If substitute is from different department, substitute's dept head approves first
            if self.substitute_employee.department != self.employee.department:
                return self.substitute_employee.department.head
            else:
                # Same department, go to direct manager
                return self.employee.manager
        elif self.status == 'substitute_pending':
            # After substitute dept head approval, go to employee's direct manager
            return self.employee.manager
        elif self.status == 'manager_pending':
            # After manager approval, go to HR
            from django.contrib.auth.models import Group
            hr_group = Group.objects.filter(name='HR').first()
            if hr_group:
                return hr_group.user_set.first()
        return None


class LeaveApproval(models.Model):
    """Track approval workflow for leave applications"""
    leave_application = models.ForeignKey(LeaveApplication, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hrms_leave_approvals')
    approval_type = models.CharField(max_length=20, choices=[
        ('substitute_dept', 'Substitute Department Head'),
        ('direct_manager', 'Direct Manager'), 
        ('hr', 'HR Approval')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    comments = models.TextField(blank=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['leave_application', 'approval_type']
        ordering = ['created_on']
    
    def __str__(self):
        return f"{self.leave_application} - {self.approval_type} - {self.status}"

# =============================================================================
# 4. TRAINING MODELS
# =============================================================================

class TrainingCategory(models.Model):
    """Training categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Training Categories"

    def __str__(self):
        return self.name

class TrainingProgram(models.Model):
    """Training programs/courses"""
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(TrainingCategory, on_delete=models.CASCADE, related_name='programs')
    description = models.TextField()
    objectives = models.TextField()
    prerequisites = models.TextField(blank=True)
    duration_hours = models.IntegerField()
    max_participants = models.IntegerField(default=20)
    training_type = models.CharField(max_length=20, choices=[
        ('classroom', 'Classroom'),
        ('online', 'Online'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('certification', 'Certification'),
        ('on_job', 'On-the-Job')
    ])
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ])
    cost_per_participant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    materials = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hrms_created_programs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.title}"

class TrainingSession(models.Model):
    """Training session instances"""
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='sessions')
    trainer_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    max_participants = models.IntegerField()
    registration_deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed')
    ], default='scheduled')
    materials_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hrms_created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.program.code} - {self.start_date.strftime('%Y-%m-%d')}"

class TrainingEnrollment(models.Model):
    """Training enrollments"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='training_enrollments')
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='training_enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('attended', 'Attended'),
        ('partial', 'Partial Attendance'),
        ('absent', 'Absent'),
        ('cancelled', 'Cancelled')
    ], default='enrolled')
    completion_status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='not_started')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ['employee', 'session']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.session.program.code}"

# =============================================================================
# 5. PERFORMANCE MANAGEMENT MODELS
# =============================================================================

class PerformanceCycle(models.Model):
    """Performance review cycles"""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    review_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('review', 'Under Review'),
        ('completed', 'Completed')
    ], default='planning')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hrms_created_cycles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_date.year})"

class PerformanceReview(models.Model):
    """Performance reviews"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='performance_reviews')
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='conducted_reviews')
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    
    # Ratings
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    goals_achievement = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    competency_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Comments
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    development_plan = models.TextField(blank=True)
    manager_comments = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('self_review', 'Self Review'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('completed', 'Completed'),
        ('acknowledged', 'Acknowledged')
    ], default='draft')
    
    # Dates
    self_review_due = models.DateField(null=True, blank=True)
    self_review_completed = models.DateTimeField(null=True, blank=True)
    manager_review_due = models.DateField(null=True, blank=True)
    manager_review_completed = models.DateTimeField(null=True, blank=True)
    final_review_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'cycle']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.cycle.name}"

# =============================================================================
# 6. PAYROLL MODELS
# =============================================================================

class PayrollPeriod(models.Model):
    """Payroll processing periods"""
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hrms_created_payroll_periods')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

class PayrollItem(models.Model):
    """Individual payroll items"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='payroll_items')
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payroll_items')
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Totals
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'payroll_period']

    def save(self, *args, **kwargs):
        # Calculate totals
        self.gross_salary = (self.basic_salary + self.housing_allowance + 
                           self.transport_allowance + self.overtime_amount + 
                           self.bonus + self.other_earnings)
        self.total_deductions = (self.tax_deduction + self.social_security + 
                               self.insurance_deduction + self.loan_deduction + 
                               self.other_deductions)
        self.net_salary = self.gross_salary - self.total_deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.payroll_period.name}"


# =============================================================================
# 9. REPORTS AND ANALYTICS MODELS
# =============================================================================

class ReportTemplate(models.Model):
    """Custom report templates"""
    REPORT_TYPES = [
        ('employee', 'Employee Report'),
        ('payroll', 'Payroll Report'),
        ('attendance', 'Attendance Report'),
        ('leave', 'Leave Report'),
        ('training', 'Training Report'),
        ('performance', 'Performance Report'),
        ('custom', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Report Configuration
    fields = models.JSONField(default=list, help_text="List of fields to include in the report")
    filters = models.JSONField(default=dict, help_text="Default filters for the report")
    grouping = models.JSONField(default=dict, help_text="Grouping configuration")
    sorting = models.JSONField(default=dict, help_text="Sorting configuration")
    
    # Export Settings
    export_formats = models.JSONField(default=list, help_text="Allowed export formats (pdf, csv, excel)")
    chart_config = models.JSONField(default=dict, help_text="Chart configuration for visual reports")
    
    # Access Control
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reports')
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='accessible_reports')
    allowed_departments = models.ManyToManyField(Department, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('hrms:custom_report_view', kwargs={'pk': self.pk})


class ScheduledReport(models.Model):
    """Scheduled reports for automatic generation and delivery"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('download', 'Download Portal'),
        ('both', 'Email & Download'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='scheduled_reports')
    
    # Schedule Configuration
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="Day of week for weekly reports (0=Monday, 6=Sunday)"
    )
    day_of_month = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month for monthly reports"
    )
    time_of_day = models.TimeField(default='09:00:00')
    
    # Delivery Configuration
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='email')
    email_recipients = models.JSONField(default=list, help_text="List of email addresses")
    email_subject = models.CharField(max_length=200, blank=True)
    email_body = models.TextField(blank=True)
    
    # Report Parameters
    date_range_type = models.CharField(max_length=20, choices=[
        ('previous_period', 'Previous Period'),
        ('current_period', 'Current Period'),
        ('custom', 'Custom Range'),
    ], default='previous_period')
    
    # Status and Control
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hrms_created_scheduled_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    def save(self, *args, **kwargs):
        if not self.next_run:
            self.calculate_next_run()
        super().save(*args, **kwargs)
    
    def calculate_next_run(self):
        """Calculate the next scheduled run time"""
        from datetime import datetime, timedelta
        import calendar
        
        now = timezone.now()
        
        if self.frequency == 'daily':
            self.next_run = now.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            if self.next_run <= now:
                self.next_run += timedelta(days=1)
                
        elif self.frequency == 'weekly':
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            self.next_run = now + timedelta(days=days_ahead)
            self.next_run = self.next_run.replace(hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            
        elif self.frequency == 'monthly':
            year = now.year
            month = now.month
            day = min(self.day_of_month, calendar.monthrange(year, month)[1])
            
            next_run = now.replace(day=day, hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            if next_run <= now:
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                day = min(self.day_of_month, calendar.monthrange(year, month)[1])
                next_run = next_run.replace(year=year, month=month, day=day)
            
            self.next_run = next_run
            
        elif self.frequency == 'quarterly':
            # Find next quarter start
            current_quarter = (now.month - 1) // 3 + 1
            next_quarter_month = current_quarter * 3 + 1
            if next_quarter_month > 12:
                next_quarter_month = 1
                year = now.year + 1
            else:
                year = now.year
            
            self.next_run = now.replace(year=year, month=next_quarter_month, day=1, 
                                      hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            
        elif self.frequency == 'yearly':
            next_run = now.replace(month=1, day=1, hour=self.time_of_day.hour, minute=self.time_of_day.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run.replace(year=now.year + 1)
            self.next_run = next_run


class ReportExecution(models.Model):
    """Track report execution history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='executions')
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE, null=True, blank=True, related_name='executions')
    
    # Execution Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField(default=dict, help_text="Parameters used for this execution")
    
    # File Information
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    export_format = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ])
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time = models.DurationField(null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    
    # Access
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hrms_generated_reports')
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.report_template.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and self.completed_at and not self.execution_time:
            self.execution_time = self.completed_at - self.started_at
        super().save(*args, **kwargs)
    
    def get_download_url(self):
        return reverse('hrms:download_report', kwargs={'pk': self.pk})


# =============================================================================
# 13. TIME & ATTENDANCE MANAGEMENT MODELS
# =============================================================================

class WorkSchedule(models.Model):
    """Work schedule templates"""
    SCHEDULE_TYPES = [
        ('fixed', 'Fixed Schedule'),
        ('flexible', 'Flexible Schedule'),
        ('shift', 'Shift-based'),
        ('remote', 'Remote Work'),
        ('hybrid', 'Hybrid Schedule'),
    ]
    
    name = models.CharField(max_length=100)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='fixed')
    description = models.TextField(blank=True)
    
    # Daily working hours
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.DurationField(default=timedelta(hours=1))  # Default 1 hour lunch
    
    # Weekly schedule
    work_days = models.JSONField(default=list)  # [1,2,3,4,5] for Mon-Fri
    weekly_hours = models.DecimalField(max_digits=4, decimal_places=2, default=40.00)
    
    # Overtime settings
    overtime_after_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)
    overtime_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)  # 1.5x rate
    
    # Grace periods
    late_grace_minutes = models.PositiveIntegerField(default=15)  # Grace period for late arrival
    early_departure_minutes = models.PositiveIntegerField(default=15)
    
    # Location settings
    require_location = models.BooleanField(default=False)
    allowed_locations = models.JSONField(default=list)  # List of allowed coordinates/addresses
    location_radius = models.PositiveIntegerField(default=100)  # Meters
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_schedule_type_display()})"
    
    @property
    def daily_hours(self):
        """Calculate expected daily working hours"""
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            if end < start:  # Next day
                end += timedelta(days=1)
            total_time = end - start
            break_time = self.break_duration or timedelta(0)
            return (total_time - break_time).total_seconds() / 3600
        return 8.0  # Default 8 hours

class EmployeeSchedule(models.Model):
    """Employee-specific schedule assignments"""
    employee = models.OneToOneField('EmployeeProfile', on_delete=models.CASCADE, related_name='work_schedule')
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE, related_name='assigned_employees')
    
    # Custom overrides
    custom_start_time = models.TimeField(null=True, blank=True)
    custom_end_time = models.TimeField(null=True, blank=True)
    custom_work_days = models.JSONField(null=True, blank=True)
    
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)
    
    # Special settings
    require_photo_verification = models.BooleanField(default=False)
    allow_remote_work = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.employee} - {self.schedule.name}"
    
    @property
    def current_schedule(self):
        """Get effective schedule details"""
        start_time = self.custom_start_time or self.schedule.start_time
        end_time = self.custom_end_time or self.schedule.end_time
        work_days = self.custom_work_days or self.schedule.work_days
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'work_days': work_days,
            'schedule': self.schedule
        }

class Attendance(models.Model):
    """Daily attendance records with comprehensive tracking"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('early_departure', 'Early Departure'),
        ('half_day', 'Half Day'),
        ('holiday', 'Holiday'),
        ('leave', 'On Leave'),
        ('remote', 'Remote Work'),
    ]
    
    employee = models.ForeignKey('EmployeeProfile', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    
    # Check in/out times
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    
    # Break times
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    total_break_time = models.DurationField(default=timedelta(0))
    
    # Time calculations
    scheduled_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    
    # Status and verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_attendance')
    
    # Location tracking
    check_in_location = models.JSONField(null=True, blank=True)  # {'lat': x, 'lng': y, 'address': '...'}
    check_out_location = models.JSONField(null=True, blank=True)
    is_remote = models.BooleanField(default=False)
    
    # Device and security
    check_in_ip = models.GenericIPAddressField(null=True, blank=True)
    check_out_ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)  # Browser, OS, device details
    
    # Photo verification
    check_in_photo = models.ImageField(upload_to='attendance/check_in/%Y/%m/', null=True, blank=True)
    check_out_photo = models.ImageField(upload_to='attendance/check_out/%Y/%m/', null=True, blank=True)
    
    # Notes and approvals
    notes = models.TextField(blank=True)
    manager_notes = models.TextField(blank=True)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_attendance')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', '-check_in']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['is_verified', 'requires_approval']),
        ]
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate hours and status on save"""
        if self.check_in and self.check_out:
            self.calculate_hours_worked()
            self.determine_status()
        super().save(*args, **kwargs)
    
    def calculate_hours_worked(self):
        """Calculate total hours worked from all sessions"""
        # First try to calculate from sessions
        total_seconds = 0
        sessions = getattr(self, 'attendance_sessions', None)
        if sessions and sessions.filter(check_out__isnull=False).exists():
            for session in sessions.filter(check_out__isnull=False):
                session_duration = session.check_out - session.check_in
                total_seconds += session_duration.total_seconds()
            
            # Convert to hours
            self.hours_worked = Decimal(str(round(total_seconds / 3600, 2)))
        elif self.check_in and self.check_out:
            # Fallback to legacy calculation
            total_time = self.check_out - self.check_in
            break_time = self.total_break_time or timedelta(0)
            
            # Calculate net working time
            net_time = total_time - break_time
            self.hours_worked = round(net_time.total_seconds() / 3600, 2)
        
        # Calculate overtime
        if self.hours_worked:
            hours_worked_decimal = Decimal(str(self.hours_worked))
            if hours_worked_decimal > self.scheduled_hours:
                self.overtime_hours = hours_worked_decimal - self.scheduled_hours
            else:
                self.overtime_hours = Decimal('0.00')
    
    def update_from_sessions(self):
        """Update legacy fields from attendance sessions"""
        sessions_queryset = getattr(self, 'attendance_sessions', None)
        if sessions_queryset:
            sessions = sessions_queryset.order_by('check_in')
            if sessions.exists():
                first_session = sessions.first()
                last_session = sessions.last()
                
                self.check_in = first_session.check_in
                self.check_in_location = first_session.check_in_location
                self.check_in_ip = first_session.check_in_ip
                
                if last_session.check_out:
                    self.check_out = last_session.check_out
                    self.check_out_location = last_session.check_out_location
                    self.check_out_ip = last_session.check_out_ip
                
                self.calculate_hours_worked()
                self.determine_status()
    
    def determine_status(self):
        """Auto-determine status based on schedule and timing"""
        if not hasattr(self.employee, 'work_schedule') or not self.employee.work_schedule:
            return
        
        schedule = self.employee.work_schedule.current_schedule
        expected_start = schedule['start_time']
        expected_end = schedule['end_time']
        
        if self.check_in and self.check_out:
            # Check if late
            check_in_time = self.check_in.time()
            grace_period = timedelta(minutes=self.employee.work_schedule.schedule.late_grace_minutes)
            expected_start_with_grace = (datetime.combine(date.today(), expected_start) + grace_period).time()
            
            if check_in_time > expected_start_with_grace:
                self.status = 'late'
            
            # Check for early departure
            check_out_time = self.check_out.time()
            early_grace = timedelta(minutes=self.employee.work_schedule.schedule.early_departure_minutes)
            expected_end_with_grace = (datetime.combine(date.today(), expected_end) - early_grace).time()
            
            if check_out_time < expected_end_with_grace:
                if self.status != 'late':
                    self.status = 'early_departure'
            
            # Check for half day
            if self.hours_worked < (self.scheduled_hours / 2):
                self.status = 'half_day'
            
            # If remote work
            if self.is_remote:
                self.status = 'remote'
            
            # If everything is normal
            if self.status == 'present' and check_in_time <= expected_start_with_grace and check_out_time >= expected_end_with_grace:
                self.status = 'present'
    
    @property
    def is_complete(self):
        """Check if attendance record is complete"""
        return bool(self.check_in and self.check_out)
    
    @property
    def duration_display(self):
        """Human readable duration"""
        if self.hours_worked:
            hours = int(self.hours_worked)
            minutes = int((self.hours_worked % 1) * 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"
    
    @property
    def check_in_delay(self):
        """Calculate delay in check-in"""
        if not (self.check_in and hasattr(self.employee, 'work_schedule') and self.employee.work_schedule):
            return None
        
        schedule = self.employee.work_schedule.current_schedule
        expected_start = schedule['start_time']
        check_in_time = self.check_in.time()
        
        expected_datetime = datetime.combine(self.date, expected_start)
        actual_datetime = datetime.combine(self.date, check_in_time)
        
        if actual_datetime > expected_datetime:
            delay = actual_datetime - expected_datetime
            return delay
        return timedelta(0)


class AttendanceSession(models.Model):
    """Individual check-in/check-out sessions within a day"""
    SESSION_TYPES = [
        ('work', 'Work Session'),
        ('meeting', 'Business Meeting'),
        ('break', 'Break/Personal'),
        ('lunch', 'Lunch Break'),
        ('other', 'Other'),
    ]
    
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='attendance_sessions')
    employee = models.ForeignKey('EmployeeProfile', on_delete=models.CASCADE, related_name='attendance_sessions')
    
    # Session timing
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    
    # Session details
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='work')
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for check-in/out (e.g., 'Meeting with client', 'Doctor appointment')")
    
    # Location tracking
    check_in_location = models.JSONField(null=True, blank=True)
    check_out_location = models.JSONField(null=True, blank=True)
    
    # Device and security
    check_in_ip = models.GenericIPAddressField(null=True, blank=True)
    check_out_ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='hrms_verified_attendance_sessions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-check_in']
        indexes = [
            models.Index(fields=['employee', 'check_in']),
            models.Index(fields=['attendance', 'check_in']),
        ]
    
    def __str__(self):
        status = "Ongoing" if not self.check_out else "Completed"
        return f"{self.employee.employee_id} - {self.check_in.strftime('%Y-%m-%d %H:%M')} - {status}"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if self.check_out:
            return self.check_out - self.check_in
        return None
    
    @property
    def duration_hours(self):
        """Get duration in hours"""
        if self.duration:
            return round(self.duration.total_seconds() / 3600, 2)
        return None
    
    def save(self, *args, **kwargs):
        """Auto-update attendance record when session changes"""
        super().save(*args, **kwargs)
        if self.attendance:
            self.attendance.update_from_sessions()
            self.attendance.save()


class AttendanceRequest(models.Model):
    """Requests for attendance modifications/approvals"""
    REQUEST_TYPES = [
        ('missed_checkin', 'Missed Check-in'),
        ('missed_checkout', 'Missed Check-out'),
        ('time_correction', 'Time Correction'),
        ('manual_entry', 'Manual Entry'),
        ('overtime_approval', 'Overtime Approval'),
        ('remote_work', 'Remote Work Request'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey('EmployeeProfile', on_delete=models.CASCADE, related_name='attendance_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='requests', null=True, blank=True)
    
    # Request details
    requested_date = models.DateField()
    requested_check_in = models.DateTimeField(null=True, blank=True)
    requested_check_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='attendance/requests/%Y/%m/', null=True, blank=True)
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['status', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.get_request_type_display()} - {self.requested_date}"

class TimeSheet(models.Model):
    """Weekly/Monthly timesheet summaries"""
    PERIOD_TYPES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    employee = models.ForeignKey('EmployeeProfile', on_delete=models.CASCADE, related_name='timesheets')
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='weekly')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Summary calculations
    total_scheduled_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_worked_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_break_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Day-wise breakdown
    attendance_summary = models.JSONField(default=dict)  # Daily attendance data
    
    # Status and approvals
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_timesheets')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Comments
    employee_comments = models.TextField(blank=True)
    manager_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'start_date', 'end_date']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'start_date']),
            models.Index(fields=['status', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.start_date} to {self.end_date}"
    
    def generate_summary(self):
        """Generate timesheet summary from attendance records"""
        attendance_records = Attendance.objects.filter(
            employee=self.employee,
            date__range=[self.start_date, self.end_date]
        )
        
        summary = {}
        total_scheduled = 0
        total_worked = 0
        total_overtime = 0
        
        for record in attendance_records:
            day_key = record.date.strftime('%Y-%m-%d')
            summary[day_key] = {
                'date': day_key,
                'check_in': record.check_in.isoformat() if record.check_in else None,
                'check_out': record.check_out.isoformat() if record.check_out else None,
                'hours_worked': float(record.hours_worked or 0),
                'overtime_hours': float(record.overtime_hours or 0),
                'scheduled_hours': float(record.scheduled_hours or 0),
                'status': record.status,
                'notes': record.notes
            }
            
            total_scheduled += record.scheduled_hours or 0
            total_worked += record.hours_worked or 0
            total_overtime += record.overtime_hours or 0
        
        self.attendance_summary = summary
        self.total_scheduled_hours = total_scheduled
        self.total_worked_hours = total_worked
        self.total_overtime_hours = total_overtime
        self.save()
    
    @property
    def attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.total_scheduled_hours > 0:
            return round((self.total_worked_hours / self.total_scheduled_hours) * 100, 2)
        return 0
    
    @property
    def week_number(self):
        """Get week number of the year"""
        return self.start_date.isocalendar()[1]


class AttendanceSettings(models.Model):
    """Model to store attendance system settings"""
    
    # Office locations for attendance tracking
    office_name = models.CharField(max_length=100, help_text="Office location name")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, help_text="Office latitude")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, help_text="Office longitude")
    radius = models.IntegerField(default=50, help_text="Allowed radius in meters")
    is_active = models.BooleanField(default=True)
    
    # Attendance rules
    allow_early_checkin = models.BooleanField(default=True, help_text="Allow check-in before scheduled time")
    early_checkin_minutes = models.IntegerField(default=30, help_text="Minutes before scheduled time")
    allow_late_checkout = models.BooleanField(default=True, help_text="Allow check-out after scheduled time")
    late_checkout_minutes = models.IntegerField(default=60, help_text="Minutes after scheduled time")
    
    # Photo verification
    require_photo = models.BooleanField(default=False, help_text="Require photo for check-in/out")
    
    # Break settings
    auto_deduct_break = models.BooleanField(default=True, help_text="Automatically deduct break time")
    default_break_minutes = models.IntegerField(default=30, help_text="Default break time in minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attendance Setting"
        verbose_name_plural = "Attendance Settings"
        
    def __str__(self):
        return f"{self.office_name} - {self.radius}m radius"


# =============================================================================
# HAWWA INTEGRATION MODELS
# =============================================================================

class VendorStaff(models.Model):
    """Link HRMS employees to Hawwa vendor system for service provider tracking"""
    
    ASSIGNMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    
    VENDOR_ROLE_CHOICES = [
        ('caretaker', 'Caretaker'),
        ('accommodation_staff', 'Accommodation Staff'),
        ('wellness_specialist', 'Wellness Specialist'),
        ('meditation_instructor', 'Meditation Instructor'),
        ('mental_health_counselor', 'Mental Health Counselor'),
        ('food_provider', 'Food Provider'),
        ('supervisor', 'Supervisor'),
        ('quality_controller', 'Quality Controller'),
        ('customer_service', 'Customer Service'),
        ('trainer', 'Trainer'),
    ]
    
    employee = models.ForeignKey(
        'EmployeeProfile', 
        on_delete=models.CASCADE, 
        related_name='vendor_assignments'
    )
    vendor_profile = models.ForeignKey(
        'vendors.VendorProfile', 
        on_delete=models.CASCADE, 
        related_name='staff_members',
        help_text="Vendor this employee is assigned to"
    )
    
    # Role and Responsibilities
    vendor_role = models.CharField(max_length=50, choices=VENDOR_ROLE_CHOICES)
    specializations = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of specializations or skills"
    )
    service_areas = models.JSONField(
        default=list, 
        blank=True,
        help_text="Geographic or service areas covered"
    )
    
    # Assignment Details
    assignment_status = models.CharField(
        max_length=20, 
        choices=ASSIGNMENT_STATUS_CHOICES, 
        default='active'
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    # Performance Tracking
    service_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        help_text="Average service rating from customers"
    )
    completed_assignments = models.IntegerField(default=0)
    total_service_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    # Availability and Scheduling
    available_days = models.JSONField(
        default=list,
        help_text="Days of week available (0=Monday, 6=Sunday)"
    )
    available_hours = models.JSONField(
        default=dict,
        help_text="Available hours per day {day: [start_hour, end_hour]}"
    )
    
    # Certification and Training
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of certifications relevant to vendor services"
    )
    training_completed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of completed training programs"
    )
    
    # Qatar Compliance
    work_permit_number = models.CharField(max_length=50, blank=True)
    work_permit_expiry = models.DateField(null=True, blank=True)
    visa_status = models.CharField(max_length=100, blank=True)
    visa_expiry = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='vendor_staff_assignments'
    )
    
    class Meta:
        unique_together = ['employee', 'vendor_profile']
        verbose_name = "Vendor Staff Assignment"
        verbose_name_plural = "Vendor Staff Assignments"
        
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.vendor_profile.business_name} ({self.vendor_role})"
    
    @property
    def is_active(self):
        """Check if assignment is currently active"""
        today = timezone.now().date()
        return (
            self.assignment_status == 'active' and
            self.start_date <= today and
            (self.end_date is None or self.end_date >= today)
        )
    
    def get_current_availability(self):
        """Get current day availability"""
        today = timezone.now().weekday()  # 0=Monday, 6=Sunday
        if today in self.available_days:
            return self.available_hours.get(str(today), [])
        return []


class ServiceAssignment(models.Model):
    """Track service assignments between vendor staff and Hawwa bookings"""
    
    ASSIGNMENT_STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    vendor_staff = models.ForeignKey(
        'VendorStaff',
        on_delete=models.CASCADE,
        related_name='service_assignments'
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    
    # Assignment Details
    assignment_status = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_STATUS_CHOICES,
        default='assigned'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    accepted_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Service Details
    service_notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # Quality and Feedback
    customer_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    customer_feedback = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Metadata
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_services'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Assignment"
        verbose_name_plural = "Service Assignments"
        ordering = ['-assigned_date']
        
    def __str__(self):
        return f"{self.vendor_staff} - Booking #{self.booking.id} ({self.assignment_status})"
    
    @property
    def duration_hours(self):
        """Calculate actual service duration in hours"""
        if self.start_date and self.completion_date:
            delta = self.completion_date - self.start_date
            return round(delta.total_seconds() / 3600, 2)
        return 0
    
    def mark_completed(self, actual_hours=None):
        """Mark assignment as completed"""
        self.assignment_status = 'completed'
        self.completion_date = timezone.now()
        if actual_hours:
            self.actual_hours = actual_hours
        self.save()
        
        # Update vendor staff statistics
        self.vendor_staff.completed_assignments += 1
        self.vendor_staff.total_service_hours += self.actual_hours
        self.vendor_staff.save()


class VendorStaffTraining(models.Model):
    """Track training programs completed by vendor staff"""
    
    TRAINING_STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    vendor_staff = models.ForeignKey(
        'VendorStaff',
        on_delete=models.CASCADE,
        related_name='training_records'
    )
    training_program = models.ForeignKey(
        'TrainingProgram',
        on_delete=models.CASCADE,
        related_name='vendor_staff_enrollments'
    )
    
    # Training Details
    status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default='enrolled'
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Performance
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Training score/grade"
    )
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_expiry = models.DateField(null=True, blank=True)
    
    # Notes
    trainer_notes = models.TextField(blank=True)
    participant_feedback = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['vendor_staff', 'training_program']
        verbose_name = "Vendor Staff Training"
        verbose_name_plural = "Vendor Staff Training Records"
        
    def __str__(self):
        return f"{self.vendor_staff} - {self.training_program.title} ({self.status})"
