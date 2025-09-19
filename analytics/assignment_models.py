"""
Smart Vendor Assignment models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class VendorAvailability(models.Model):
    """
    Track vendor availability schedules and capacity
    """
    AVAILABILITY_TYPES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
        ('break', 'On Break'),
        ('vacation', 'On Vacation'),
    ]
    
    REPEAT_PATTERNS = [
        ('none', 'No Repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='availability_schedule'
    )
    
    # Date and time information
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Availability status
    status = models.CharField(max_length=20, choices=AVAILABILITY_TYPES, default='available')
    
    # Capacity management
    max_concurrent_bookings = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    current_bookings = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Repeat settings
    repeat_pattern = models.CharField(max_length=20, choices=REPEAT_PATTERNS, default='none')
    repeat_until = models.DateField(blank=True, null=True)
    
    # Notes and metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vendor Availability'
        verbose_name_plural = 'Vendor Availabilities'
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['vendor', 'date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.date} {self.start_time}-{self.end_time}"
    
    @property
    def is_available(self):
        """Check if vendor has capacity for more bookings"""
        return self.status == 'available' and self.current_bookings < self.max_concurrent_bookings
    
    @property
    def capacity_percentage(self):
        """Calculate current capacity utilization percentage"""
        if self.max_concurrent_bookings == 0:
            return 100
        return (self.current_bookings / self.max_concurrent_bookings) * 100


class VendorWorkload(models.Model):
    """
    Track vendor workload and performance metrics for assignment decisions
    """
    WORKLOAD_STATUS = [
        ('light', 'Light Load'),
        ('moderate', 'Moderate Load'),
        ('heavy', 'Heavy Load'),
        ('overloaded', 'Overloaded'),
    ]
    
    vendor = models.OneToOneField(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='current_workload'
    )
    
    # Current workload metrics
    active_bookings = models.IntegerField(default=0)
    pending_bookings = models.IntegerField(default=0)
    completed_today = models.IntegerField(default=0)
    total_revenue_today = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Capacity metrics
    daily_booking_limit = models.IntegerField(default=10)
    weekly_booking_limit = models.IntegerField(default=50)
    monthly_booking_limit = models.IntegerField(default=200)
    
    # Performance metrics for assignment scoring
    avg_response_time_minutes = models.IntegerField(default=60)  # Average response time in minutes
    completion_rate_7days = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    customer_satisfaction_7days = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
    
    # Assignment preferences
    preferred_service_radius_km = models.IntegerField(default=50)  # Preferred service radius
    accepts_urgent_bookings = models.BooleanField(default=True)
    accepts_weekend_bookings = models.BooleanField(default=True)
    accepts_evening_bookings = models.BooleanField(default=True)
    
    # Current status
    workload_status = models.CharField(max_length=20, choices=WORKLOAD_STATUS, default='light')
    last_assignment = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vendor Workload'
        verbose_name_plural = 'Vendor Workloads'
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.workload_status}"
    
    @property
    def workload_score(self):
        """Calculate workload score (0-100, higher = more available)"""
        # Base score starts at 100
        score = 100
        
        # Reduce score based on active bookings
        if self.daily_booking_limit > 0:
            daily_utilization = (self.active_bookings / self.daily_booking_limit) * 100
            score -= daily_utilization
        
        # Adjust for pending bookings
        score -= (self.pending_bookings * 5)  # Each pending booking reduces score by 5
        
        # Adjust for workload status
        status_penalties = {
            'light': 0,
            'moderate': 10,
            'heavy': 25,
            'overloaded': 50,
        }
        score -= status_penalties.get(self.workload_status, 0)
        
        return max(0, min(100, score))
    
    def update_workload_status(self):
        """Update workload status based on current metrics"""
        if self.daily_booking_limit > 0:
            utilization = (self.active_bookings + self.pending_bookings) / self.daily_booking_limit
            
            if utilization <= 0.3:
                self.workload_status = 'light'
            elif utilization <= 0.6:
                self.workload_status = 'moderate'
            elif utilization <= 0.9:
                self.workload_status = 'heavy'
            else:
                self.workload_status = 'overloaded'
        else:
            self.workload_status = 'light'
        
        self.save(update_fields=['workload_status'])


class VendorAssignment(models.Model):
    """
    Track vendor assignments to bookings with scoring and reasoning
    """
    ASSIGNMENT_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('auto_assigned', 'Auto Assigned'),
        ('manual_override', 'Manual Override'),
        ('cancelled', 'Cancelled'),
    ]
    
    ASSIGNMENT_METHODS = [
        ('smart_ai', 'Smart AI Assignment'),
        ('manual', 'Manual Assignment'),
        ('vendor_request', 'Vendor Request'),
        ('customer_preference', 'Customer Preference'),
        ('emergency', 'Emergency Assignment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='vendor_assignments'
    )
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assignment details
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='pending')
    assignment_method = models.CharField(max_length=20, choices=ASSIGNMENT_METHODS, default='smart_ai')
    is_primary = models.BooleanField(default=True)  # Primary vs backup assignment
    
    # AI scoring details
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    location_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    availability_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    workload_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    preference_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Distance and logistics
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    estimated_travel_time_minutes = models.IntegerField(blank=True, null=True)
    
    # Assignment reasoning
    assignment_reasoning = models.JSONField(default=dict, help_text="AI reasoning for assignment")
    confidence_level = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    declined_at = models.DateTimeField(blank=True, null=True)
    
    # Response details
    vendor_response_time_minutes = models.IntegerField(blank=True, null=True)
    decline_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Vendor Assignment'
        verbose_name_plural = 'Vendor Assignments'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['assigned_at']),
        ]
        unique_together = ['booking', 'vendor']  # Prevent duplicate assignments
    
    def __str__(self):
        return f"{self.booking.booking_number} → {self.vendor.business_name} ({self.status})"
    
    def accept_assignment(self):
        """Mark assignment as accepted"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.responded_at = timezone.now()
        
        if self.assigned_at:
            time_diff = self.responded_at - self.assigned_at
            self.vendor_response_time_minutes = int(time_diff.total_seconds() / 60)
        
        self.save()
        
        # Update vendor workload
        workload, created = VendorWorkload.objects.get_or_create(vendor=self.vendor)
        workload.active_bookings += 1
        workload.last_assignment = timezone.now()
        workload.update_workload_status()
    
    def decline_assignment(self, reason=""):
        """Mark assignment as declined"""
        self.status = 'declined'
        self.declined_at = timezone.now()
        self.responded_at = timezone.now()
        self.decline_reason = reason
        
        if self.assigned_at:
            time_diff = self.responded_at - self.assigned_at
            self.vendor_response_time_minutes = int(time_diff.total_seconds() / 60)
        
        self.save()


class AssignmentPreference(models.Model):
    """
    Store customer and vendor preferences for assignments
    """
    PREFERENCE_TYPES = [
        ('customer', 'Customer Preference'),
        ('vendor', 'Vendor Preference'),
        ('system', 'System Preference'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preference_type = models.CharField(max_length=20, choices=PREFERENCE_TYPES)
    
    # Related entities
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_preferences',
        blank=True,
        null=True
    )
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='assignment_preferences',
        blank=True,
        null=True
    )
    service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    
    # Preference settings
    preferred_vendors = models.ManyToManyField(
        'vendors.VendorProfile',
        related_name='preferred_by',
        blank=True
    )
    excluded_vendors = models.ManyToManyField(
        'vendors.VendorProfile',
        related_name='excluded_by',
        blank=True
    )
    
    # Geographic preferences
    max_distance_km = models.IntegerField(default=50)
    preferred_areas = models.JSONField(default=list, help_text="List of preferred service areas")
    
    # Timing preferences
    preferred_time_slots = models.JSONField(default=list, help_text="Preferred time slots")
    avoid_rush_hours = models.BooleanField(default=False)
    
    # Quality preferences
    min_vendor_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    require_certification = models.BooleanField(default=False)
    
    # Priority settings
    priority_weight = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.00'))
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Assignment Preference'
        verbose_name_plural = 'Assignment Preferences'
        ordering = ['-priority_weight', '-created_at']
    
    def __str__(self):
        entity = self.customer or self.vendor or "System"
        return f"{self.preference_type} - {entity}"


class AssignmentLog(models.Model):
    """
    Log all assignment activities for analytics and debugging
    """
    LOG_TYPES = [
        ('assignment_created', 'Assignment Created'),
        ('assignment_accepted', 'Assignment Accepted'),
        ('assignment_declined', 'Assignment Declined'),
        ('assignment_cancelled', 'Assignment Cancelled'),
        ('reassignment', 'Reassignment'),
        ('auto_assignment', 'Auto Assignment'),
        ('manual_override', 'Manual Override'),
        ('system_error', 'System Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        VendorAssignment,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    # Log details
    log_type = models.CharField(max_length=30, choices=LOG_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict)
    
    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Performance metrics
    processing_time_ms = models.IntegerField(blank=True, null=True)
    system_load = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Assignment Log'
        verbose_name_plural = 'Assignment Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['assignment', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.log_type} - {self.assignment} at {self.timestamp}"