from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    QualityScore, PerformanceMetrics, VendorRanking, QualityCertification
)


@admin.register(QualityScore)
class QualityScoreAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'overall_score', 'grade', 'calculated_at', 
        'period_start', 'period_end', 'total_bookings'
    ]
    list_filter = ['calculated_at', 'period_start', 'trend_direction']
    search_fields = ['vendor__business_name', 'vendor__user__username']
    readonly_fields = ['calculated_at']
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor', 'period_start', 'period_end', 'calculated_at')
        }),
        ('Overall Score', {
            'fields': ('overall_score', 'weights')
        }),
        ('Component Scores', {
            'fields': (
                'customer_ratings_score',
                'completion_rate_score', 
                'response_time_score',
                'repeat_customers_score',
                'performance_trends_score'
            )
        }),
        ('Supporting Metrics', {
            'fields': (
                'total_bookings',
                'completed_bookings',
                'avg_rating',
                'avg_response_time_hours',
                'repeat_customer_rate',
                'trend_direction'
            )
        }),
    )
    
    def grade(self, obj):
        color_map = {
            'A+': '#28a745', 'A': '#28a745',
            'B+': '#6f42c1', 'B': '#6f42c1',
            'C+': '#fd7e14', 'C': '#fd7e14',
            'D': '#dc3545', 'F': '#dc3545'
        }
        grade = obj.grade
        color = color_map.get(grade, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, grade
        )
    grade.short_description = 'Grade'


@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'date', 'completion_rate_display', 'avg_rating',
        'bookings_completed', 'revenue'
    ]
    list_filter = ['date', 'vendor']
    search_fields = ['vendor__business_name', 'vendor__user__username']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'date')
        }),
        ('Booking Metrics', {
            'fields': (
                'bookings_received',
                'bookings_accepted',
                'bookings_completed',
                'bookings_cancelled',
                'bookings_no_show'
            )
        }),
        ('Response Metrics', {
            'fields': (
                'avg_response_time_minutes',
                'first_response_rate'
            )
        }),
        ('Customer Satisfaction', {
            'fields': (
                'total_ratings',
                'avg_rating',
                'five_star_ratings',
                'four_star_ratings',
                'three_star_ratings',
                'two_star_ratings',
                'one_star_ratings'
            )
        }),
        ('Financial Metrics', {
            'fields': (
                'revenue',
                'commission_paid',
                'avg_booking_value'
            )
        }),
        ('Customer Retention', {
            'fields': (
                'new_customers',
                'repeat_customers',
                'total_unique_customers'
            )
        }),
        ('Operational Metrics', {
            'fields': (
                'on_time_completion_rate',
                'rework_rate'
            )
        }),
    )
    
    def completion_rate_display(self, obj):
        rate = obj.completion_rate
        if rate >= 95:
            color = '#28a745'
        elif rate >= 85:
            color = '#6f42c1'
        elif rate >= 75:
            color = '#fd7e14'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = 'Completion Rate'


@admin.register(VendorRanking)
class VendorRankingAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'overall_rank', 'service_category', 'percentile_display',
        'quality_score', 'ranking_date'
    ]
    list_filter = ['ranking_date', 'service_category']
    search_fields = ['vendor__business_name', 'vendor__user__username']
    ordering = ['overall_rank']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'service_category', 'ranking_date')
        }),
        ('Rankings', {
            'fields': (
                'overall_rank',
                'quality_rank',
                'performance_rank',
                'customer_satisfaction_rank',
                'total_vendors'
            )
        }),
        ('Scores', {
            'fields': (
                'quality_score',
                'performance_score',
                'customer_satisfaction_score'
            )
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
    )
    
    def percentile_display(self, obj):
        percentile = obj.percentile
        if percentile >= 90:
            color = '#28a745'
        elif percentile >= 75:
            color = '#6f42c1'
        elif percentile >= 50:
            color = '#fd7e14'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, percentile
        )
    percentile_display.short_description = 'Percentile'


@admin.register(QualityCertification)
class QualityCertificationAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'certification_type', 'awarded_date', 'valid_until',
        'is_valid_display', 'achieved_quality_score'
    ]
    list_filter = [
        'certification_type', 'awarded_date', 'is_active',
        'valid_until'
    ]
    search_fields = ['vendor__business_name', 'vendor__user__username']
    date_hierarchy = 'awarded_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'certification_type', 'is_active')
        }),
        ('Dates', {
            'fields': ('awarded_date', 'valid_until')
        }),
        ('Requirements', {
            'fields': (
                'min_quality_score',
                'achieved_quality_score',
                'criteria_met'
            )
        }),
    )
    
    def is_valid_display(self, obj):
        is_valid = obj.is_valid()
        if is_valid:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Expired</span>'
            )
    is_valid_display.short_description = 'Status'


# Custom admin actions
@admin.action(description='Recalculate quality scores')
def recalculate_quality_scores(modeladmin, request, queryset):
    from .services import quality_scoring_engine
    
    updated_count = 0
    for vendor in queryset:
        try:
            quality_scoring_engine.calculate_quality_score(vendor)
            updated_count += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error calculating score for {vendor}: {e}",
                level='ERROR'
            )
    
    modeladmin.message_user(
        request,
        f"Successfully recalculated quality scores for {updated_count} vendors."
    )


# Add the action to VendorProfile admin if it exists
try:
    from vendors.admin import VendorProfileAdmin
    VendorProfileAdmin.actions = list(VendorProfileAdmin.actions or []) + [recalculate_quality_scores]
except ImportError:
    pass
