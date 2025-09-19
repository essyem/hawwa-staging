from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json
import uuid

User = get_user_model()

class WorkflowTemplate(models.Model):
    """Template for reusable workflows"""
    WORKFLOW_TYPES = [
        ('booking_processing', 'Booking Processing'),
        ('vendor_assignment', 'Vendor Assignment'),
        ('quality_check', 'Quality Check'),
        ('payment_processing', 'Payment Processing'),
        ('customer_onboarding', 'Customer Onboarding'),
        ('service_delivery', 'Service Delivery'),
        ('complaint_resolution', 'Complaint Resolution'),
        ('performance_review', 'Performance Review'),
    ]
    
    TRIGGER_TYPES = [
        ('manual', 'Manual Trigger'),
        ('time_based', 'Time-Based'),
        ('event_based', 'Event-Based'),
        ('condition_based', 'Condition-Based'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Workflow template name")
    description = models.TextField(help_text="Detailed workflow description")
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES, default='manual')
    
    # Configuration
    steps_config = models.JSONField(default=dict, help_text="Workflow steps configuration")
    conditions_config = models.JSONField(default=dict, help_text="Workflow conditions and rules")
    automation_rules = models.JSONField(default=dict, help_text="Automation rules and triggers")
    
    # Settings
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    max_parallel_instances = models.IntegerField(default=10)
    estimated_duration_minutes = models.IntegerField(default=60)
    priority_level = models.IntegerField(default=5, help_text="1=Highest, 10=Lowest")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_workflows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['priority_level', 'name']
        verbose_name = "Workflow Template"
        verbose_name_plural = "Workflow Templates"
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def create_instance(self, triggered_by=None, context_data=None):
        """Create a new workflow instance from this template"""
        return WorkflowInstance.objects.create(
            template=self,
            triggered_by=triggered_by,
            context_data=context_data or {},
            status='pending'
        )

class WorkflowInstance(models.Model):
    """Active workflow instance"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('waiting_approval', 'Waiting Approval'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='instances')
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_step = models.IntegerField(default=0)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Context and data
    context_data = models.JSONField(default=dict, help_text="Instance-specific data")
    execution_log = models.JSONField(default=list, help_text="Execution log entries")
    error_details = models.JSONField(default=dict, help_text="Error information if failed")
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Relations
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_workflows')
    
    # Booking relation (if applicable)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Workflow Instance"
        verbose_name_plural = "Workflow Instances"
    
    def __str__(self):
        return f"{self.template.name} - {self.status}"
    
    def start_execution(self):
        """Start workflow execution"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()
        
        # Log start
        self.add_log_entry('Workflow execution started')
    
    def add_log_entry(self, message, level='info', details=None):
        """Add entry to execution log"""
        entry = {
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message,
            'details': details or {}
        }
        
        if isinstance(self.execution_log, list):
            self.execution_log.append(entry)
        else:
            self.execution_log = [entry]
        
        self.save(update_fields=['execution_log'])
    
    def calculate_duration(self):
        """Calculate workflow duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
    
    def is_overdue(self):
        """Check if workflow is overdue"""
        if self.estimated_completion and self.status in ['pending', 'running']:
            return timezone.now() > self.estimated_completion
        return False

class WorkflowStep(models.Model):
    """Individual step in workflow instance"""
    STEP_TYPES = [
        ('task', 'Task'),
        ('decision', 'Decision'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('api_call', 'API Call'),
        ('assignment', 'Assignment'),
        ('quality_check', 'Quality Check'),
        ('delay', 'Delay'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    name = models.CharField(max_length=200)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Step-specific configuration")
    input_data = models.JSONField(default=dict, help_text="Input data for this step")
    output_data = models.JSONField(default=dict, help_text="Output data from this step")
    
    # Execution details
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Dependencies
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['workflow_instance', 'step_number']
        unique_together = ['workflow_instance', 'step_number']
        verbose_name = "Workflow Step"
        verbose_name_plural = "Workflow Steps"
    
    def __str__(self):
        return f"Step {self.step_number}: {self.name}"
    
    def can_execute(self):
        """Check if step can be executed (dependencies met)"""
        return all(dep.status == 'completed' for dep in self.depends_on.all())
    
    def execute(self):
        """Execute this workflow step"""
        if not self.can_execute():
            return False
        
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
        
        # Step execution logic would go here
        # This is a placeholder for actual step execution
        
        return True

class AutomationRule(models.Model):
    """Rules for automated workflow triggering and actions"""
    RULE_TYPES = [
        ('trigger', 'Trigger Rule'),
        ('condition', 'Condition Rule'),
        ('action', 'Action Rule'),
        ('escalation', 'Escalation Rule'),
    ]
    
    TRIGGER_EVENTS = [
        ('booking_created', 'Booking Created'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('payment_received', 'Payment Received'),
        ('service_completed', 'Service Completed'),
        ('customer_complaint', 'Customer Complaint'),
        ('vendor_assigned', 'Vendor Assigned'),
        ('quality_score_updated', 'Quality Score Updated'),
        ('sla_violation', 'SLA Violation'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_EVENTS, null=True, blank=True)
    
    # Rule configuration
    conditions = models.JSONField(default=dict, help_text="Rule conditions")
    actions = models.JSONField(default=dict, help_text="Actions to perform")
    
    # Targeting
    workflow_template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, null=True, blank=True)
    applies_to_types = models.JSONField(default=list, help_text="Entity types this rule applies to")
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=5)
    max_executions_per_day = models.IntegerField(default=100)
    
    # Tracking
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"
    
    def can_execute(self):
        """Check if rule can be executed today"""
        today = timezone.now().date()
        today_executions = self.execution_count if self.last_executed and self.last_executed.date() == today else 0
        return today_executions < self.max_executions_per_day
    
    def execute(self, context=None):
        """Execute automation rule"""
        if not self.can_execute():
            return False
        
        self.execution_count += 1
        self.last_executed = timezone.now()
        self.save()
        
        # Rule execution logic would go here
        return True

class VendorPerformanceMetric(models.Model):
    """Vendor performance tracking"""
    METRIC_TYPES = [
        ('quality_score', 'Quality Score'),
        ('response_time', 'Response Time'),
        ('completion_rate', 'Completion Rate'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('punctuality', 'Punctuality'),
        ('cost_effectiveness', 'Cost Effectiveness'),
        ('availability', 'Availability'),
        ('expertise_level', 'Expertise Level'),
    ]
    
    vendor = models.ForeignKey('vendors.VendorProfile', on_delete=models.CASCADE, related_name='performance_metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    max_value = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('100.00'))
    
    # Context
    service = models.ForeignKey('services.Service', on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Calculation details
    calculation_method = models.CharField(max_length=50, default='manual')
    data_points_used = models.IntegerField(default=1)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    
    # Metadata
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name = "Vendor Performance Metric"
        verbose_name_plural = "Vendor Performance Metrics"
    
    def __str__(self):
        return f"{self.vendor.name} - {self.metric_type}: {self.value}/{self.max_value}"
    
    def get_percentage_score(self):
        """Get score as percentage"""
        if self.max_value > 0:
            return (self.value / self.max_value) * 100
        return 0
    
    def get_performance_level(self):
        """Get performance level based on score"""
        percentage = self.get_percentage_score()
        if percentage >= 90:
            return 'excellent'
        elif percentage >= 80:
            return 'good'
        elif percentage >= 70:
            return 'average'
        elif percentage >= 60:
            return 'below_average'
        else:
            return 'poor'

class OperationalAlert(models.Model):
    """System alerts for operational issues"""
    ALERT_TYPES = [
        ('sla_violation', 'SLA Violation'),
        ('quality_drop', 'Quality Drop'),
        ('vendor_unavailable', 'Vendor Unavailable'),
        ('workflow_failed', 'Workflow Failed'),
        ('performance_issue', 'Performance Issue'),
        ('resource_overload', 'Resource Overload'),
        ('customer_complaint', 'Customer Complaint'),
        ('system_error', 'System Error'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Relations
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey('vendors.VendorProfile', on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    alert_data = models.JSONField(default=dict, help_text="Additional alert data")
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-severity', '-created_at']
        verbose_name = "Operational Alert"
        verbose_name_plural = "Operational Alerts"
    
    def __str__(self):
        return f"{self.title} ({self.severity})"
    
    def acknowledge(self, user):
        """Acknowledge alert"""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user, notes=''):
        """Resolve alert"""
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def get_age_hours(self):
        """Get alert age in hours"""
        return (timezone.now() - self.created_at).total_seconds() / 3600
