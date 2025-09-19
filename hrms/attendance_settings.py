from django.contrib import admin
from django.db import models

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

@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ['office_name', 'latitude', 'longitude', 'radius', 'is_active']
    list_filter = ['is_active']
    search_fields = ['office_name']
    fieldsets = (
        ('Office Location', {
            'fields': ('office_name', 'latitude', 'longitude', 'radius', 'is_active')
        }),
        ('Attendance Rules', {
            'fields': ('allow_early_checkin', 'early_checkin_minutes', 'allow_late_checkout', 'late_checkout_minutes')
        }),
        ('Additional Settings', {
            'fields': ('require_photo', 'auto_deduct_break', 'default_break_minutes')
        }),
    )
