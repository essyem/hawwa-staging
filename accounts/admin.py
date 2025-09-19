from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test

from .models import User

def superuser_required(view_func):
    """Decorator to require superuser access."""
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@admin.action(description='Unregister selected users (Superuser only)')
def unregister_users(modeladmin, request, queryset):
    """Custom admin action to unregister users - only for superusers."""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can unregister users.")
        return
    
    # Prevent superusers from unregistering themselves
    if request.user in queryset:
        messages.error(request, "You cannot unregister yourself.")
        return
    
    # Count users by type for confirmation message
    user_types = queryset.values('user_type').annotate(count=Count('user_type'))
    type_summary = ', '.join([f"{item['count']} {item['user_type'].title()}" for item in user_types])
    
    # Deactivate users and log the action
    updated = queryset.update(
        is_active=False,
        is_staff=False,
        is_verified=False
    )
    
    # Log the unregistration
    for user in queryset:
        admin.site._registry[User].log_change(
            request, 
            user, 
            f"User unregistered by superuser {request.user.email}"
        )
    
    messages.success(
        request, 
        f"Successfully unregistered {updated} users: {type_summary}. "
        f"Users can be reactivated if needed."
    )

@admin.action(description='Reactivate selected users (Superuser only)')
def reactivate_users(modeladmin, request, queryset):
    """Custom admin action to reactivate users - only for superusers."""
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can reactivate users.")
        return
    
    # Only reactivate inactive users
    inactive_users = queryset.filter(is_active=False)
    updated = inactive_users.update(is_active=True)
    
    # Log the reactivation
    for user in inactive_users:
        admin.site._registry[User].log_change(
            request, 
            user, 
            f"User reactivated by superuser {request.user.email}"
        )
    
    messages.success(
        request, 
        f"Successfully reactivated {updated} users."
    )

@admin.action(description='Verify selected users')
def verify_users(modeladmin, request, queryset):
    """Custom admin action to verify users."""
    updated = queryset.filter(is_verified=False).update(is_verified=True)
    messages.success(request, f"Successfully verified {updated} users.")

@admin.action(description='Unverify selected users')
def unverify_users(modeladmin, request, queryset):
    """Custom admin action to unverify users."""
    updated = queryset.filter(is_verified=True).update(is_verified=False)
    messages.success(request, f"Successfully unverified {updated} users.")

class UserAdmin(BaseUserAdmin):
    """Enhanced admin configuration for the custom User model."""
    ordering = ('email',)
    list_display = (
        'email', 'get_full_name', 'user_type', 'is_active', 
        'is_verified', 'is_staff', 'date_joined', 'last_login_formatted',
        'profile_completion'
    )
    list_filter = (
        'user_type', 'is_active', 'is_staff', 'is_superuser', 'is_verified',
        'date_joined', 'last_login', 'receive_emails', 'receive_sms'
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('date_joined', 'last_login', 'profile_completion')
    list_per_page = 25
    list_max_show_all = 100
    
    # Custom actions
    actions = [unregister_users, reactivate_users, verify_users, unverify_users]
    
    def get_full_name(self, obj):
        """Return the full name of the user."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def last_login_formatted(self, obj):
        """Return formatted last login date."""
        if obj.last_login:
            time_diff = timezone.now() - obj.last_login
            if time_diff.days == 0:
                return format_html('<span style="color: green;">Today</span>')
            elif time_diff.days <= 7:
                return format_html('<span style="color: orange;">{} days ago</span>', time_diff.days)
            elif time_diff.days <= 30:
                return format_html('<span style="color: red;">{} days ago</span>', time_diff.days)
            else:
                return format_html('<span style="color: gray;">Long ago</span>')
        return format_html('<span style="color: red;">Never</span>')
    last_login_formatted.short_description = 'Last Login'
    last_login_formatted.admin_order_field = 'last_login'
    
    def profile_completion(self, obj):
        """Calculate and display profile completion percentage."""
        fields_to_check = [
            'first_name', 'last_name', 'phone', 'address', 
            'city', 'state', 'country', 'profile_picture'
        ]
        completed_fields = sum(1 for field in fields_to_check if getattr(obj, field))
        percentage = (completed_fields / len(fields_to_check)) * 100
        
        if percentage >= 80:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
            
        return format_html(
            '<span style="color: {};">{}</span>', 
            color, f'{percentage:.0f}%'
        )
    profile_completion.short_description = 'Profile Completion'
    
    def get_queryset(self, request):
        """Optimize queryset for admin interface."""
        qs = super().get_queryset(request)
        return qs.select_related().prefetch_related('groups', 'user_permissions')
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete users."""
        return request.user.is_superuser
    
    def get_actions(self, request):
        """Filter actions based on user permissions."""
        actions = super().get_actions(request)
        
        # Only superusers can see unregister/reactivate actions
        if not request.user.is_superuser:
            if 'unregister_users' in actions:
                del actions['unregister_users']
            if 'reactivate_users' in actions:
                del actions['reactivate_users']
                
        return actions
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'phone', 'profile_picture')}),
        (_('User Type'), {'fields': ('user_type',)}),
        (_('Location'), {'fields': ('address', 'city', 'state', 'country', 'postal_code')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                                      'groups', 'user_permissions')}),
        (_('Notification Preferences'), {'fields': ('receive_emails', 'receive_sms')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff')
        }),
    )

admin.site.register(User, UserAdmin)
