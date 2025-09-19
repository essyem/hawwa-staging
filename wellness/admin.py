from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    WellnessCategory, 
    WellnessProgram, 
    WellnessSession, 
    WellnessEnrollment,
    WellnessReview
)

@admin.register(WellnessCategory)
class WellnessCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'

class WellnessSessionInline(admin.TabularInline):
    model = WellnessSession
    extra = 1

@admin.register(WellnessProgram)
class WellnessProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'provider', 'duration', 'status', 'featured', 'created_at']
    list_filter = ['status', 'featured', 'category']
    search_fields = ['name', 'short_description', 'description']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    inlines = [WellnessSessionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'provider', 'status', 'featured')
        }),
        (_('Details'), {
            'fields': ('short_description', 'description', 'benefits', 'duration')
        }),
        (_('Media'), {
            'fields': ('image', 'video_url')
        }),
    )

class WellnessEnrollmentInline(admin.TabularInline):
    model = WellnessEnrollment
    extra = 0
    readonly_fields = ['enrolled_at']
    fields = ['user', 'status', 'enrolled_at', 'notes']

@admin.register(WellnessSession)
class WellnessSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'program', 'date', 'start_time', 'end_time', 'is_online', 'status', 'max_participants']
    list_filter = ['status', 'is_online', 'date']
    search_fields = ['title', 'program__name', 'location', 'notes']
    date_hierarchy = 'date'
    inlines = [WellnessEnrollmentInline]
    fieldsets = (
        (None, {
            'fields': ('program', 'title', 'status')
        }),
        (_('Schedule'), {
            'fields': ('date', 'start_time', 'end_time')
        }),
        (_('Location'), {
            'fields': ('is_online', 'location', 'online_link')
        }),
        (_('Capacity'), {
            'fields': ('max_participants', 'notes')
        }),
    )

@admin.register(WellnessEnrollment)
class WellnessEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'program', 'session', 'status', 'enrolled_at']
    list_filter = ['status', 'enrolled_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'program__name', 'session__title']
    readonly_fields = ['enrolled_at']
    date_hierarchy = 'enrolled_at'

@admin.register(WellnessReview)
class WellnessReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'program', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'program__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
