from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AIBuddyProfile, Conversation, Message, 
    WellnessTracking, Milestone, CareRecommendation
)


@admin.register(AIBuddyProfile)
class AIBuddyProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'personality_type', 'created_at']
    list_filter = ['personality_type', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('AI Configuration', {
            'fields': ('personality_type', 'preferences', 'conversation_context')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['id', 'timestamp']
    fields = ['message_type', 'content', 'timestamp']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'message_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'message_count', 'created_at', 'updated_at']
    inlines = [MessageInline]
    
    fieldsets = (
        ('Conversation Details', {
            'fields': ('user', 'title', 'is_active')
        }),
        ('Statistics', {
            'fields': ('message_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['conversation__title', 'content']
    readonly_fields = ['id', 'timestamp']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('conversation', 'message_type', 'content')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        })
    )
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(WellnessTracking)
class WellnessTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'mood', 'energy_level', 
        'sleep_hours', 'symptoms_count', 'created_at'
    ]
    list_filter = ['date', 'mood', 'energy_level', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'notes']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date')
        }),
        ('Wellness Metrics', {
            'fields': ('mood', 'energy_level', 'sleep_hours')
        }),
        ('Additional Information', {
            'fields': ('physical_symptoms', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def symptoms_count(self, obj):
        return len(obj.physical_symptoms) if obj.physical_symptoms else 0
    symptoms_count.short_description = 'Symptoms Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'milestone_type', 'title', 'is_achieved', 
        'achieved_date', 'created_at'
    ]
    list_filter = ['milestone_type', 'is_achieved', 'achieved_date', 'created_at']
    search_fields = ['user__email', 'title', 'description']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Milestone Information', {
            'fields': ('user', 'milestone_type', 'title', 'description')
        }),
        ('Achievement', {
            'fields': ('is_achieved', 'achieved_date')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CareRecommendation)
class CareRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'title', 'recommendation_type', 'priority', 
        'is_completed', 'created_at'
    ]
    list_filter = ['recommendation_type', 'priority', 'is_completed', 'created_at']
    search_fields = ['user__email', 'title', 'description']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('user', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('recommendation_type', 'priority')
        }),
        ('Status', {
            'fields': ('is_completed',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_completed', 'mark_as_pending']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(is_completed=True)
        self.message_user(request, f'{updated} recommendations marked as completed.')
    mark_as_completed.short_description = 'Mark selected recommendations as completed'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(is_completed=False)
        self.message_user(request, f'{updated} recommendations marked as pending.')
    mark_as_pending.short_description = 'Mark selected recommendations as pending'


# Customize admin site header
admin.site.site_header = "Hawwa AI Buddy Administration"
admin.site.site_title = "AI Buddy Admin"
admin.site.index_title = "Welcome to AI Buddy Administration"
