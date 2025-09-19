from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json

class QualityScore(models.Model):
    """
    Quality scoring system for vendors with multi-factor analysis
    """
    
    SCORE_CATEGORIES = (
        ('customer_ratings', _('Customer Ratings')),
        ('completion_rate', _('Completion Rate')),
        ('response_time', _('Response Time')),
        ('repeat_customers', _('Repeat Customers')),
        ('performance_trends', _('Performance Trends')),
    )
    
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='quality_scores'
    )
    
    # Overall quality score (0-100)
    overall_score = models.DecimalField(
        _('Overall Quality Score'),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    # Individual component scores (0-100)
    customer_ratings_score = models.DecimalField(
        _('Customer Ratings Score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    completion_rate_score = models.DecimalField(
        _('Completion Rate Score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    response_time_score = models.DecimalField(
        _('Response Time Score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    repeat_customers_score = models.DecimalField(
        _('Repeat Customers Score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    performance_trends_score = models.DecimalField(
        _('Performance Trends Score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Weights for each component (should add up to 1.0)
    weights = models.JSONField(
        _('Score Weights'),
        default=dict,
        help_text=_('JSON object with weights for each scoring component')
    )
    
    # Metrics used for calculation
    total_bookings = models.PositiveIntegerField(_('Total Bookings'), default=0)
    completed_bookings = models.PositiveIntegerField(_('Completed Bookings'), default=0)
    avg_rating = models.DecimalField(_('Average Rating'), max_digits=3, decimal_places=2, default=0)
    avg_response_time_hours = models.DecimalField(_('Avg Response Time (Hours)'), max_digits=5, decimal_places=2, default=0)
    repeat_customer_rate = models.DecimalField(_('Repeat Customer Rate'), max_digits=5, decimal_places=2, default=0)
    trend_direction = models.CharField(
        _('Trend Direction'),
        max_length=20,
        choices=(
            ('improving', _('Improving')),
            ('stable', _('Stable')),
            ('declining', _('Declining')),
        ),
        default='stable'
    )
    
    # Metadata
    calculated_at = models.DateTimeField(_('Calculated At'), auto_now=True)
    period_start = models.DateField(_('Period Start'))
    period_end = models.DateField(_('Period End'))
    
    class Meta:
        verbose_name = _('Quality Score')
        verbose_name_plural = _('Quality Scores')
        ordering = ['-calculated_at']
        unique_together = ['vendor', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.overall_score:.1f}/100"
    
    @property
    def grade(self):
        """Return letter grade based on overall score"""
        if self.overall_score >= 90:
            return 'A+'
        elif self.overall_score >= 85:
            return 'A'
        elif self.overall_score >= 80:
            return 'B+'
        elif self.overall_score >= 75:
            return 'B'
        elif self.overall_score >= 70:
            return 'C+'
        elif self.overall_score >= 65:
            return 'C'
        elif self.overall_score >= 60:
            return 'D'
        else:
            return 'F'


class PerformanceMetrics(models.Model):
    """
    Real-time performance metrics tracking for vendors
    """
    
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='analytics_performance_metrics'
    )
    
    # Time period
    date = models.DateField(_('Date'))
    
    # Booking metrics
    bookings_received = models.PositiveIntegerField(_('Bookings Received'), default=0)
    bookings_accepted = models.PositiveIntegerField(_('Bookings Accepted'), default=0)
    bookings_completed = models.PositiveIntegerField(_('Bookings Completed'), default=0)
    bookings_cancelled = models.PositiveIntegerField(_('Bookings Cancelled'), default=0)
    bookings_no_show = models.PositiveIntegerField(_('No Shows'), default=0)
    
    # Response metrics
    avg_response_time_minutes = models.PositiveIntegerField(_('Avg Response Time (Minutes)'), default=0)
    first_response_rate = models.DecimalField(
        _('First Response Rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Percentage of bookings responded to within SLA')
    )
    
    # Customer satisfaction
    total_ratings = models.PositiveIntegerField(_('Total Ratings'), default=0)
    avg_rating = models.DecimalField(_('Average Rating'), max_digits=3, decimal_places=2, default=0)
    five_star_ratings = models.PositiveIntegerField(_('5-Star Ratings'), default=0)
    four_star_ratings = models.PositiveIntegerField(_('4-Star Ratings'), default=0)
    three_star_ratings = models.PositiveIntegerField(_('3-Star Ratings'), default=0)
    two_star_ratings = models.PositiveIntegerField(_('2-Star Ratings'), default=0)
    one_star_ratings = models.PositiveIntegerField(_('1-Star Ratings'), default=0)
    
    # Financial metrics
    revenue = models.DecimalField(_('Revenue'), max_digits=10, decimal_places=2, default=0)
    commission_paid = models.DecimalField(_('Commission Paid'), max_digits=10, decimal_places=2, default=0)
    avg_booking_value = models.DecimalField(_('Avg Booking Value'), max_digits=8, decimal_places=2, default=0)
    
    # Customer retention
    new_customers = models.PositiveIntegerField(_('New Customers'), default=0)
    repeat_customers = models.PositiveIntegerField(_('Repeat Customers'), default=0)
    total_unique_customers = models.PositiveIntegerField(_('Total Unique Customers'), default=0)
    
    # Operational metrics
    on_time_completion_rate = models.DecimalField(
        _('On-Time Completion Rate'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    rework_rate = models.DecimalField(
        _('Rework Rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Percentage of jobs requiring rework')
    )
    
    class Meta:
        verbose_name = _('Performance Metrics')
        verbose_name_plural = _('Performance Metrics')
        unique_together = ['vendor', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.date}"
    
    @property
    def completion_rate(self):
        """Calculate completion rate percentage"""
        if self.bookings_accepted == 0:
            return 0
        return (self.bookings_completed / self.bookings_accepted) * 100
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate percentage"""
        if self.bookings_received == 0:
            return 0
        return (self.bookings_accepted / self.bookings_received) * 100
    
    @property
    def repeat_customer_rate(self):
        """Calculate repeat customer rate percentage"""
        if self.total_unique_customers == 0:
            return 0
        return (self.repeat_customers / self.total_unique_customers) * 100


class VendorRanking(models.Model):
    """
    Vendor ranking system based on quality scores and performance
    """
    
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='rankings'
    )
    
    service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.CASCADE,
        related_name='vendor_rankings',
        null=True,
        blank=True,
        help_text=_('Category-specific ranking (null for overall)')
    )
    
    # Rankings
    overall_rank = models.PositiveIntegerField(_('Overall Rank'))
    quality_rank = models.PositiveIntegerField(_('Quality Rank'))
    performance_rank = models.PositiveIntegerField(_('Performance Rank'))
    customer_satisfaction_rank = models.PositiveIntegerField(_('Customer Satisfaction Rank'))
    
    # Scores used for ranking
    quality_score = models.DecimalField(_('Quality Score'), max_digits=5, decimal_places=2)
    performance_score = models.DecimalField(_('Performance Score'), max_digits=5, decimal_places=2)
    customer_satisfaction_score = models.DecimalField(_('Customer Satisfaction Score'), max_digits=5, decimal_places=2)
    
    # Total vendors in comparison
    total_vendors = models.PositiveIntegerField(_('Total Vendors'))
    
    # Metadata
    ranking_date = models.DateField(_('Ranking Date'), auto_now_add=True)
    period_start = models.DateField(_('Period Start'))
    period_end = models.DateField(_('Period End'))
    
    class Meta:
        verbose_name = _('Vendor Ranking')
        verbose_name_plural = _('Vendor Rankings')
        ordering = ['overall_rank']
        unique_together = ['vendor', 'service_category', 'ranking_date']
    
    def __str__(self):
        category = self.service_category.name if self.service_category else "Overall"
        return f"{self.vendor.business_name} - Rank #{self.overall_rank} ({category})"
    
    @property
    def percentile(self):
        """Calculate percentile based on overall rank"""
        if self.total_vendors == 0:
            return 0
        return ((self.total_vendors - self.overall_rank + 1) / self.total_vendors) * 100


class QualityCertification(models.Model):
    """
    Quality certifications and badges for vendors
    """
    
    CERTIFICATION_TYPES = (
        ('quality_excellence', _('Quality Excellence')),
        ('customer_favorite', _('Customer Favorite')),
        ('reliable_service', _('Reliable Service')),
        ('fast_response', _('Fast Response')),
        ('top_performer', _('Top Performer')),
        ('trusted_vendor', _('Trusted Vendor')),
    )
    
    vendor = models.ForeignKey(
        'vendors.VendorProfile',
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    
    certification_type = models.CharField(
        _('Certification Type'),
        max_length=30,
        choices=CERTIFICATION_TYPES
    )
    
    awarded_date = models.DateField(_('Awarded Date'), auto_now_add=True)
    valid_until = models.DateField(_('Valid Until'))
    
    # Requirements met
    min_quality_score = models.DecimalField(_('Min Quality Score Required'), max_digits=5, decimal_places=2)
    achieved_quality_score = models.DecimalField(_('Achieved Quality Score'), max_digits=5, decimal_places=2)
    
    # Additional criteria
    criteria_met = models.JSONField(
        _('Criteria Met'),
        default=dict,
        help_text=_('JSON object with specific criteria and values')
    )
    
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    class Meta:
        verbose_name = _('Quality Certification')
        verbose_name_plural = _('Quality Certifications')
        ordering = ['-awarded_date']
        unique_together = ['vendor', 'certification_type', 'awarded_date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.get_certification_type_display()}"
    
    def is_valid(self):
        """Check if certification is still valid"""
        return self.is_active and self.valid_until >= timezone.now().date()


# Import assignment models from assignment_models.py
from .assignment_models import (
    VendorAvailability,
    VendorWorkload,
    VendorAssignment,
    AssignmentPreference,
    AssignmentLog
)
