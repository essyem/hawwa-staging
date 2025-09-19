from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
from datetime import datetime, timedelta
import json

class AnalyticsMetric(models.Model):
    """Store analytics metrics for business intelligence."""
    METRIC_TYPES = (
        ('revenue', _('Revenue Metric')),
        ('booking', _('Booking Metric')),
        ('customer', _('Customer Metric')),
        ('service', _('Service Metric')),
        ('operational', _('Operational Metric')),
        ('financial', _('Financial Metric')),
    )
    
    AGGREGATION_TYPES = (
        ('sum', _('Sum')),
        ('count', _('Count')),
        ('avg', _('Average')),
        ('max', _('Maximum')),
        ('min', _('Minimum')),
        ('percentage', _('Percentage')),
    )
    
    name = models.CharField(_("Metric Name"), max_length=100)
    metric_type = models.CharField(_("Metric Type"), max_length=20, choices=METRIC_TYPES)
    aggregation_type = models.CharField(_("Aggregation Type"), max_length=20, choices=AGGREGATION_TYPES)
    value = models.DecimalField(_("Value"), max_digits=15, decimal_places=2)
    date_recorded = models.DateTimeField(_("Date Recorded"), default=timezone.now)
    period_start = models.DateTimeField(_("Period Start"))
    period_end = models.DateTimeField(_("Period End"))
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Analytics Metric")
        verbose_name_plural = _("Analytics Metrics")
        ordering = ['-date_recorded']
        indexes = [
            models.Index(fields=['metric_type', 'date_recorded']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.name}: {self.value} ({self.date_recorded.strftime('%Y-%m-%d')})"

class ReportTemplate(models.Model):
    """Template for generating business reports."""
    REPORT_TYPES = (
        ('financial', _('Financial Report')),
        ('operational', _('Operational Report')),
        ('customer', _('Customer Report')),
        ('service', _('Service Report')),
        ('executive', _('Executive Summary')),
        ('custom', _('Custom Report')),
    )
    
    CHART_TYPES = (
        ('line', _('Line Chart')),
        ('bar', _('Bar Chart')),
        ('pie', _('Pie Chart')),
        ('doughnut', _('Doughnut Chart')),
        ('area', _('Area Chart')),
        ('scatter', _('Scatter Plot')),
        ('table', _('Data Table')),
    )
    
    name = models.CharField(_("Report Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    report_type = models.CharField(_("Report Type"), max_length=20, choices=REPORT_TYPES)
    chart_type = models.CharField(_("Chart Type"), max_length=20, choices=CHART_TYPES)
    
    # Data Configuration
    data_source = models.CharField(_("Data Source"), max_length=100, 
                                  help_text=_("Model or view to query data from"))
    filters = models.JSONField(_("Filters"), default=dict, blank=True,
                              help_text=_("JSON filters to apply to data"))
    grouping = models.CharField(_("Grouping Field"), max_length=100, blank=True,
                               help_text=_("Field to group data by"))
    aggregation_field = models.CharField(_("Aggregation Field"), max_length=100, blank=True)
    aggregation_type = models.CharField(_("Aggregation Type"), max_length=20, 
                                       choices=AnalyticsMetric.AGGREGATION_TYPES, default='count')
    
    # Display Configuration
    x_axis_label = models.CharField(_("X-Axis Label"), max_length=100, blank=True)
    y_axis_label = models.CharField(_("Y-Axis Label"), max_length=100, blank=True)
    chart_title = models.CharField(_("Chart Title"), max_length=200, blank=True)
    color_scheme = models.CharField(_("Color Scheme"), max_length=50, default='default')
    
    # Scheduling
    is_automated = models.BooleanField(_("Automated Generation"), default=False)
    schedule_frequency = models.CharField(_("Schedule Frequency"), max_length=20, 
                                        choices=[
                                            ('daily', _('Daily')),
                                            ('weekly', _('Weekly')),
                                            ('monthly', _('Monthly')),
                                            ('quarterly', _('Quarterly')),
                                        ], blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='report_templates')
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Report Template")
        verbose_name_plural = _("Report Templates")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class ReportGeneration(models.Model):
    """Track generated reports and their data."""
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE,
                                related_name='generations')
    generated_at = models.DateTimeField(_("Generated At"), auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name='generated_reports')
    
    # Report Data
    data = models.JSONField(_("Report Data"), default=dict)
    chart_config = models.JSONField(_("Chart Configuration"), default=dict)
    summary_stats = models.JSONField(_("Summary Statistics"), default=dict)
    
    # Period Information
    period_start = models.DateTimeField(_("Period Start"))
    period_end = models.DateTimeField(_("Period End"))
    
    # Status
    is_cached = models.BooleanField(_("Cached"), default=True)
    cache_expires_at = models.DateTimeField(_("Cache Expires At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Report Generation")
        verbose_name_plural = _("Report Generations")
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['template', 'generated_at']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_cache_valid(self):
        """Check if cached report is still valid."""
        if not self.is_cached or not self.cache_expires_at:
            return False
        return timezone.now() < self.cache_expires_at

class BusinessInsight(models.Model):
    """Store AI-generated or rule-based business insights."""
    INSIGHT_TYPES = (
        ('trend', _('Trend Analysis')),
        ('anomaly', _('Anomaly Detection')),
        ('opportunity', _('Business Opportunity')),
        ('risk', _('Risk Alert')),
        ('recommendation', _('Recommendation')),
        ('forecast', _('Forecast')),
    )
    
    PRIORITY_LEVELS = (
        ('low', _('Low Priority')),
        ('medium', _('Medium Priority')),
        ('high', _('High Priority')),
        ('critical', _('Critical')),
    )
    
    title = models.CharField(_("Insight Title"), max_length=200)
    description = models.TextField(_("Description"))
    insight_type = models.CharField(_("Insight Type"), max_length=20, choices=INSIGHT_TYPES)
    priority = models.CharField(_("Priority"), max_length=20, choices=PRIORITY_LEVELS, default='medium')
    
    # Data Context
    related_metric = models.ForeignKey(AnalyticsMetric, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='insights')
    supporting_data = models.JSONField(_("Supporting Data"), default=dict)
    confidence_score = models.DecimalField(_("Confidence Score"), max_digits=5, decimal_places=2,
                                          default=Decimal('0.00'),
                                          help_text=_("Confidence level (0-100)"))
    
    # Action Items
    recommended_actions = models.TextField(_("Recommended Actions"), blank=True)
    impact_estimate = models.CharField(_("Impact Estimate"), max_length=100, blank=True)
    
    # Status
    is_acknowledged = models.BooleanField(_("Acknowledged"), default=False)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='acknowledged_insights')
    acknowledged_at = models.DateTimeField(_("Acknowledged At"), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Business Insight")
        verbose_name_plural = _("Business Insights")
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['insight_type', 'priority']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    def acknowledge(self, user):
        """Mark insight as acknowledged by user."""
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()

class DashboardWidget(models.Model):
    """Configure dashboard widgets for data visualization."""
    WIDGET_TYPES = (
        ('metric_card', _('Metric Card')),
        ('chart', _('Chart Widget')),
        ('table', _('Data Table')),
        ('progress', _('Progress Bar')),
        ('gauge', _('Gauge Chart')),
        ('map', _('Geographic Map')),
        ('timeline', _('Timeline')),
        ('alert', _('Alert Widget')),
    )
    
    SIZE_OPTIONS = (
        ('small', _('Small (1x1)')),
        ('medium', _('Medium (2x1)')),
        ('large', _('Large (2x2)')),
        ('wide', _('Wide (3x1)')),
        ('tall', _('Tall (1x2)')),
        ('extra_large', _('Extra Large (3x2)')),
    )
    
    name = models.CharField(_("Widget Name"), max_length=100)
    widget_type = models.CharField(_("Widget Type"), max_length=20, choices=WIDGET_TYPES)
    size = models.CharField(_("Size"), max_length=20, choices=SIZE_OPTIONS, default='medium')
    
    # Layout
    position_x = models.PositiveIntegerField(_("Position X"), default=0)
    position_y = models.PositiveIntegerField(_("Position Y"), default=0)
    width = models.PositiveIntegerField(_("Width"), default=2)
    height = models.PositiveIntegerField(_("Height"), default=1)
    
    # Data Configuration
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE,
                                       null=True, blank=True, related_name='widgets')
    metric_source = models.CharField(_("Metric Source"), max_length=100, blank=True)
    refresh_interval = models.PositiveIntegerField(_("Refresh Interval (seconds)"), default=300)
    
    # Display Configuration
    title = models.CharField(_("Display Title"), max_length=200)
    subtitle = models.CharField(_("Subtitle"), max_length=200, blank=True)
    show_legend = models.BooleanField(_("Show Legend"), default=True)
    show_grid = models.BooleanField(_("Show Grid"), default=True)
    color_scheme = models.CharField(_("Color Scheme"), max_length=50, default='default')
    custom_config = models.JSONField(_("Custom Configuration"), default=dict, blank=True)
    
    # Access Control
    is_public = models.BooleanField(_("Public Widget"), default=True)
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                          related_name='dashboard_widgets')
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='created_widgets')
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Dashboard Widget")
        verbose_name_plural = _("Dashboard Widgets")
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"
