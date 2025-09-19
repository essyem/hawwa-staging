from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    WorkflowTemplate, WorkflowInstance, 
    AutomationRule, OperationalAlert, VendorPerformanceMetric
)

@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow_type', 'is_active', 'trigger_type', 'created_at']
    list_filter = ['workflow_type', 'is_active', 'trigger_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'workflow_type', 'trigger_type')
        }),
        ('Configuration', {
            'fields': ('steps_config', 'conditions_config', 'automation_rules')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_approval', 'max_parallel_instances', 'estimated_duration_minutes', 'priority_level')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'status_badge', 'assigned_to', 'current_step', 'progress_bar', 'created_at']
    list_filter = ['status', 'template__workflow_type', 'created_at']
    search_fields = ['template__name', 'assigned_to__username', 'assigned_to__email']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Workflow Information', {
            'fields': ('template', 'assigned_to', 'status')
        }),
        ('Progress', {
            'fields': ('current_step', 'progress_percentage', 'estimated_completion')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
        ('Data', {
            'fields': ('context_data', 'execution_log', 'error_details'),
            'classes': ('collapse',)
        }),
    )
    
    def template_name(self, obj):
        return obj.template.name
    template_name.short_description = 'Template'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'running': '#007cba',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage or 0
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 4px;">'
            '<div style="width: {}%; background-color: #007cba; height: 20px; border-radius: 4px; '
            'text-align: center; color: white; font-size: 12px; line-height: 20px;">{:.0f}%</div></div>',
            percentage, percentage
        )
    progress_bar.short_description = 'Progress'

@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'priority', 'execution_count', 'last_executed']
    list_filter = ['rule_type', 'is_active', 'priority', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['execution_count', 'last_executed', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active', 'priority')
        }),
        ('Rule Configuration', {
            'fields': ('rule_type', 'trigger_event', 'conditions')
        }),
        ('Actions & Targeting', {
            'fields': ('actions', 'workflow_template', 'applies_to_types')
        }),
        ('Limits & Statistics', {
            'fields': ('max_executions_per_day', 'execution_count', 'last_executed', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OperationalAlert)
class OperationalAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity_badge', 'alert_type', 'status', 'created_at']
    list_filter = ['severity', 'alert_type', 'status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'acknowledged_at', 'resolved_at']
    
    actions = ['mark_acknowledged', 'mark_resolved']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('title', 'description', 'alert_type', 'severity', 'status')
        }),
        ('Relations', {
            'fields': ('workflow_instance', 'vendor', 'booking')
        }),
        ('Assignment & Resolution', {
            'fields': ('assigned_to', 'acknowledged_by', 'resolved_by', 'resolution_notes')
        }),
        ('Data & Timing', {
            'fields': ('alert_data', 'created_at', 'acknowledged_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def severity_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            colors.get(obj.severity, '#6c757d'),
            obj.get_severity_display().upper()
        )
    severity_badge.short_description = 'Severity'
    
    def mark_acknowledged(self, request, queryset):
        updated = queryset.update(
            status='acknowledged',
            acknowledged_by=request.user,
            acknowledged_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts marked as acknowledged.')
    mark_acknowledged.short_description = 'Mark selected alerts as acknowledged'
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(
            status='resolved',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'

@admin.register(VendorPerformanceMetric)
class VendorPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'metric_type', 'value', 'max_value', 'percentage_score', 'recorded_at']
    list_filter = ['metric_type', 'recorded_at']
    search_fields = ['vendor__business_name', 'metric_type']
    readonly_fields = ['recorded_at', 'percentage_score', 'performance_level']
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor', 'metric_type')
        }),
        ('Metric Data', {
            'fields': ('value', 'max_value', 'percentage_score', 'performance_level')
        }),
        ('Calculation Details', {
            'fields': ('calculation_method', 'data_points_used', 'confidence_level')
        }),
        ('Context & Recording', {
            'fields': ('service', 'booking', 'recorded_by', 'recorded_at', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def percentage_score(self, obj):
        percentage = obj.get_percentage_score()
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 60 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, percentage
        )
    percentage_score.short_description = 'Score %'
    
    def performance_level(self, obj):
        return obj.get_performance_level().replace('_', ' ').title()
# Admin will be configured after migrations are created
