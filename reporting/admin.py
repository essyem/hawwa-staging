from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    AnalyticsMetric, ReportTemplate, ReportGeneration, 
    BusinessInsight, DashboardWidget
)

# Phase 2 Enhanced Data Analytics - Advanced Business Intelligence

@admin.register(AnalyticsMetric)
class AnalyticsMetricAdmin(admin.ModelAdmin):
    """Admin interface for analytics metrics."""
    list_display = (
        'name', 'metric_type_colored', 'value_formatted', 'aggregation_type',
        'period_display', 'date_recorded'
    )
    list_filter = ('metric_type', 'aggregation_type', 'date_recorded')
    search_fields = ('name', 'metadata')
    readonly_fields = ('date_recorded',)
    date_hierarchy = 'date_recorded'
    list_per_page = 25
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('name', 'metric_type', 'aggregation_type', 'value')
        }),
        ('Time Period', {
            'fields': ('period_start', 'period_end', 'date_recorded')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def metric_type_colored(self, obj):
        """Display metric type with color coding."""
        colors = {
            'revenue': 'green',
            'booking': 'blue',
            'customer': 'orange',
            'service': 'purple',
            'operational': 'brown',
            'financial': 'darkgreen'
        }
        color = colors.get(obj.metric_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_metric_type_display()
        )
    metric_type_colored.short_description = 'Type'
    metric_type_colored.admin_order_field = 'metric_type'
    
    def value_formatted(self, obj):
        """Display formatted metric value."""
        if obj.metric_type in ['revenue', 'financial']:
            return format_html('<strong>QAR {}</strong>', f'{obj.value:.2f}')
        elif obj.aggregation_type == 'percentage':
            return format_html('<strong>{}%</strong>', f'{obj.value:.1f}')
        else:
            return format_html('<strong>{}</strong>', f'{obj.value:.0f}')
    value_formatted.short_description = 'Value'
    value_formatted.admin_order_field = 'value'
    
    def period_display(self, obj):
        """Display period in readable format."""
        start = obj.period_start.strftime('%Y-%m-%d')
        end = obj.period_end.strftime('%Y-%m-%d')
        return f"{start} to {end}"
    period_display.short_description = 'Period'

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin interface for report templates."""
    list_display = (
        'name', 'report_type_colored', 'chart_type', 'is_automated',
        'schedule_frequency', 'is_active', 'created_at'
    )
    list_filter = ('report_type', 'chart_type', 'is_automated', 'is_active')
    search_fields = ('name', 'description', 'data_source')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'report_type', 'chart_type', 'is_active')
        }),
        ('Data Configuration', {
            'fields': ('data_source', 'filters', 'grouping', 'aggregation_field', 'aggregation_type')
        }),
        ('Display Settings', {
            'fields': ('chart_title', 'x_axis_label', 'y_axis_label', 'color_scheme')
        }),
        ('Automation', {
            'fields': ('is_automated', 'schedule_frequency'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def report_type_colored(self, obj):
        """Display report type with color coding."""
        colors = {
            'financial': 'green',
            'operational': 'blue',
            'customer': 'orange',
            'service': 'purple',
            'executive': 'red',
            'custom': 'gray'
        }
        color = colors.get(obj.report_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_report_type_display()
        )
    report_type_colored.short_description = 'Report Type'
    report_type_colored.admin_order_field = 'report_type'
    
    def save_model(self, request, obj, form, change):
        """Set created_by field."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReportGeneration)
class ReportGenerationAdmin(admin.ModelAdmin):
    """Admin interface for report generations."""
    list_display = (
        'template_link', 'generated_at', 'generated_by', 'period_display',
        'cache_status', 'data_size'
    )
    list_filter = ('generated_at', 'is_cached', 'template__report_type')
    search_fields = ('template__name', 'generated_by__email')
    readonly_fields = ('generated_at', 'data_size', 'cache_status')
    date_hierarchy = 'generated_at'
    list_per_page = 25
    
    fieldsets = (
        ('Generation Info', {
            'fields': ('template', 'generated_at', 'generated_by')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Data', {
            'fields': ('data', 'chart_config', 'summary_stats'),
            'classes': ('collapse',)
        }),
        ('Caching', {
            'fields': ('is_cached', 'cache_expires_at'),
            'classes': ('collapse',)
        })
    )
    
    def template_link(self, obj):
        """Display template with link."""
        url = reverse('admin:reporting_reporttemplate_change', args=[obj.template.id])
        return format_html('<a href="{}">{}</a>', url, obj.template.name)
    template_link.short_description = 'Template'
    template_link.admin_order_field = 'template__name'
    
    def period_display(self, obj):
        """Display period in readable format."""
        start = obj.period_start.strftime('%Y-%m-%d')
        end = obj.period_end.strftime('%Y-%m-%d')
        return f"{start} to {end}"
    period_display.short_description = 'Period'
    
    def cache_status(self, obj):
        """Display cache status."""
        if obj.is_cached and obj.is_cache_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        elif obj.is_cached:
            return format_html('<span style="color: orange;">⚠ Expired</span>')
        else:
            return format_html('<span style="color: gray;">Not Cached</span>')
    cache_status.short_description = 'Cache'
    
    def data_size(self, obj):
        """Display approximate data size."""
        if obj.data:
            import json
            size = len(json.dumps(obj.data))
            if size > 1024:
                return f"{size//1024}KB"
            return f"{size}B"
        return "Empty"
    data_size.short_description = 'Data Size'

@admin.register(BusinessInsight)
class BusinessInsightAdmin(admin.ModelAdmin):
    """Admin interface for business insights."""
    list_display = (
        'title', 'insight_type_colored', 'priority_colored', 'confidence_score',
        'acknowledgment_status', 'created_at'
    )
    list_filter = ('insight_type', 'priority', 'is_acknowledged', 'is_active')
    search_fields = ('title', 'description', 'recommended_actions')
    readonly_fields = ('created_at', 'acknowledged_at')
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['acknowledge_insights', 'mark_inactive']
    
    fieldsets = (
        ('Insight Information', {
            'fields': ('title', 'description', 'insight_type', 'priority')
        }),
        ('Data Context', {
            'fields': ('related_metric', 'supporting_data', 'confidence_score')
        }),
        ('Recommendations', {
            'fields': ('recommended_actions', 'impact_estimate')
        }),
        ('Status', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at', 'is_active')
        }),
        ('Lifecycle', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )
    
    def insight_type_colored(self, obj):
        """Display insight type with color coding."""
        colors = {
            'trend': 'blue',
            'anomaly': 'orange',
            'opportunity': 'green',
            'risk': 'red',
            'recommendation': 'purple',
            'forecast': 'teal'
        }
        color = colors.get(obj.insight_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_insight_type_display()
        )
    insight_type_colored.short_description = 'Type'
    insight_type_colored.admin_order_field = 'insight_type'
    
    def priority_colored(self, obj):
        """Display priority with color coding."""
        colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red'
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_colored.short_description = 'Priority'
    priority_colored.admin_order_field = 'priority'
    
    def acknowledgment_status(self, obj):
        """Display acknowledgment status."""
        if obj.is_acknowledged:
            return format_html(
                '<span style="color: green;">✓ Acknowledged</span><br><small>by {}</small>',
                obj.acknowledged_by.get_full_name() if obj.acknowledged_by else 'Unknown'
            )
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    acknowledgment_status.short_description = 'Status'
    
    @admin.action(description='Mark insights as acknowledged')
    def acknowledge_insights(self, request, queryset):
        """Mark selected insights as acknowledged."""
        updated = 0
        for insight in queryset.filter(is_acknowledged=False):
            insight.acknowledge(request.user)
            updated += 1
        messages.success(request, f"Successfully acknowledged {updated} insights.")
    
    @admin.action(description='Mark insights as inactive')
    def mark_inactive(self, request, queryset):
        """Mark selected insights as inactive."""
        updated = queryset.update(is_active=False)
        messages.success(request, f"Successfully marked {updated} insights as inactive.")

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Admin interface for dashboard widgets."""
    list_display = (
        'title', 'widget_type_colored', 'size', 'position_display',
        'refresh_interval', 'is_active', 'created_at'
    )
    list_filter = ('widget_type', 'size', 'is_active', 'is_public')
    search_fields = ('title', 'name', 'subtitle')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Widget Information', {
            'fields': ('name', 'title', 'subtitle', 'widget_type', 'size')
        }),
        ('Layout', {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        ('Data Configuration', {
            'fields': ('report_template', 'metric_source', 'refresh_interval')
        }),
        ('Display Options', {
            'fields': ('show_legend', 'show_grid', 'color_scheme', 'custom_config'),
            'classes': ('collapse',)
        }),
        ('Access Control', {
            'fields': ('is_public', 'allowed_users', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def widget_type_colored(self, obj):
        """Display widget type with color coding."""
        colors = {
            'metric_card': 'blue',
            'chart': 'green',
            'table': 'purple',
            'progress': 'orange',
            'gauge': 'red',
            'map': 'teal',
            'timeline': 'brown',
            'alert': 'red'
        }
        color = colors.get(obj.widget_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_widget_type_display()
        )
    widget_type_colored.short_description = 'Type'
    widget_type_colored.admin_order_field = 'widget_type'
    
    def position_display(self, obj):
        """Display widget position."""
        return f"({obj.position_x}, {obj.position_y})"
    position_display.short_description = 'Position'
    
    def save_model(self, request, obj, form, change):
        """Set created_by field."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Enhanced KPI Dashboard with real-time analytics
def get_analytics_dashboard_context():
    """Get comprehensive analytics dashboard context."""
    try:
        from accounts.models import User
        from services.models import Service
        from bookings.models import Booking
        from financial.models import Invoice, Payment
        
        # Current date ranges
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        
        # Financial Analytics
        total_revenue = Invoice.objects.filter(status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        monthly_revenue = Invoice.objects.filter(
            status='paid',
            paid_date__gte=current_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_month_revenue = Invoice.objects.filter(
            status='paid',
            paid_date__gte=last_month_start,
            paid_date__lte=last_month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Revenue growth calculation
        if last_month_revenue > 0:
            revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100
        else:
            revenue_growth = 100 if monthly_revenue > 0 else 0
        
        # Booking Analytics
        total_bookings = Booking.objects.count()
        monthly_bookings = Booking.objects.filter(
            created_at__gte=current_month_start
        ).count()
        
        booking_conversion = Booking.objects.filter(
            status='confirmed'
        ).count() / total_bookings * 100 if total_bookings > 0 else 0
        
        # Customer Analytics
        total_customers = User.objects.count()
        active_customers = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        customer_retention = (active_customers / total_customers * 100) if total_customers > 0 else 0
        
        # Service Performance
        top_services = Service.objects.annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count')[:5]
        
        return {
            'total_revenue': f"QAR {total_revenue:.2f}",
            'monthly_revenue': f"QAR {monthly_revenue:.2f}",
            'revenue_growth': f"{revenue_growth:.1f}%",
            'total_bookings': total_bookings,
            'monthly_bookings': monthly_bookings,
            'booking_conversion': f"{booking_conversion:.1f}%",
            'total_customers': total_customers,
            'active_customers': active_customers,
            'customer_retention': f"{customer_retention:.1f}%",
            'top_services': top_services
        }
        
    except Exception as e:
        return {'error': str(e)}
