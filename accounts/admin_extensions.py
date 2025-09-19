"""
Enhanced admin extensions for superuser management and platform administration.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import User


class HawwaAdminSite(AdminSite):
    """
    Custom admin site for Hawwa platform with enhanced features.
    """
    site_header = _('Hawwa Platform Administration')
    site_title = _('Hawwa Admin')
    index_title = _('Platform Administration Dashboard')
    site_url = '/'
    
    def get_urls(self):
        """Add custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path('platform-stats/', self.admin_view(self.platform_stats_view), name='platform_stats'),
            path('user-management/', self.admin_view(self.user_management_view), name='user_management'),
            path('bulk-user-actions/', self.admin_view(self.bulk_user_actions_view), name='bulk_user_actions'),
            path('system-health/', self.admin_view(self.system_health_view), name='system_health'),
        ]
        return custom_urls + urls
    
    @method_decorator(staff_member_required)
    def platform_stats_view(self, request):
        """Custom view for platform statistics."""
        # Calculate platform statistics
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'new_users_30d': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
        }
        
        # User type distribution
        user_types = User.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly user growth
        monthly_growth = []
        for i in range(6):
            month_start = now.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
            
            count = User.objects.filter(
                date_joined__gte=month_start,
                date_joined__lt=month_end
            ).count()
            
            monthly_growth.append({
                'month': month_start.strftime('%B %Y'),
                'count': count
            })
        
        context = {
            'stats': stats,
            'user_types': user_types,
            'monthly_growth': list(reversed(monthly_growth)),
            'title': 'Platform Statistics',
        }
        
        return render(request, 'admin/platform_stats.html', context)
    
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def user_management_view(self, request):
        """Enhanced user management view for superusers only."""
        users = User.objects.select_related().prefetch_related('groups')
        
        # Filter by query parameters
        user_type = request.GET.get('user_type')
        status = request.GET.get('status')
        search = request.GET.get('search')
        
        if user_type:
            users = users.filter(user_type=user_type)
        
        if status == 'active':
            users = users.filter(is_active=True)
        elif status == 'inactive':
            users = users.filter(is_active=False)
        elif status == 'verified':
            users = users.filter(is_verified=True)
        elif status == 'unverified':
            users = users.filter(is_verified=False)
        
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(users, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'users': page_obj,
            'user_types': User.USER_TYPE_CHOICES,
            'current_filters': {
                'user_type': user_type,
                'status': status,
                'search': search,
            },
            'title': 'Advanced User Management',
        }
        
        return render(request, 'admin/user_management.html', context)
    
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    @method_decorator(csrf_exempt)
    def bulk_user_actions_view(self, request):
        """Handle bulk user actions (AJAX endpoint)."""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            user_ids = data.get('user_ids', [])
            
            if not user_ids:
                return JsonResponse({'error': 'No users selected'}, status=400)
            
            users = User.objects.filter(id__in=user_ids)
            
            # Prevent superuser from acting on themselves
            if request.user.id in user_ids:
                return JsonResponse({'error': 'Cannot perform action on yourself'}, status=400)
            
            success_count = 0
            
            if action == 'unregister':
                # Deactivate users
                success_count = users.update(
                    is_active=False,
                    is_staff=False,
                    is_verified=False
                )
                
                # Log the action
                for user in users:
                    admin.site._registry[User].log_change(
                        request, user, f"Bulk unregistered by superuser {request.user.email}"
                    )
                
            elif action == 'reactivate':
                success_count = users.filter(is_active=False).update(is_active=True)
                
            elif action == 'verify':
                success_count = users.filter(is_verified=False).update(is_verified=True)
                
            elif action == 'unverify':
                success_count = users.filter(is_verified=True).update(is_verified=False)
                
            elif action == 'make_staff':
                if not request.user.is_superuser:
                    return JsonResponse({'error': 'Only superusers can promote to staff'}, status=403)
                success_count = users.filter(is_staff=False).update(is_staff=True)
                
            elif action == 'remove_staff':
                if not request.user.is_superuser:
                    return JsonResponse({'error': 'Only superusers can demote staff'}, status=403)
                # Don't demote superusers
                success_count = users.filter(is_staff=True, is_superuser=False).update(is_staff=False)
                
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully performed {action} on {success_count} users',
                'affected_count': success_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @method_decorator(staff_member_required)
    def system_health_view(self, request):
        """System health dashboard."""
        from django.db import connection
        from django.core.cache import cache
        
        # Database health
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = 'healthy'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        # Cache health
        try:
            cache.set('health_check', 'ok', 30)
            cache_result = cache.get('health_check')
            cache_status = 'healthy' if cache_result == 'ok' else 'error'
        except Exception as e:
            cache_status = f'error: {str(e)}'
        
        # System statistics
        system_stats = {
            'db_status': db_status,
            'cache_status': cache_status,
            'total_users': User.objects.count(),
            'active_sessions': len([s for s in connection.queries if 'session' in str(s)]),
            'admin_users': User.objects.filter(is_staff=True).count(),
            'last_login_24h': User.objects.filter(
                last_login__gte=timezone.now() - timedelta(hours=24)
            ).count(),
        }
        
        context = {
            'system_stats': system_stats,
            'title': 'System Health Dashboard',
        }
        
        return render(request, 'admin/system_health.html', context)

    def index(self, request, extra_context=None):
        """Enhanced admin index with custom dashboard."""
        extra_context = extra_context or {}
        
        if request.user.is_authenticated:
            # Quick stats for dashboard
            extra_context.update({
                'quick_stats': {
                    'total_users': User.objects.count(),
                    'active_users': User.objects.filter(is_active=True).count(),
                    'new_users_today': User.objects.filter(
                        date_joined__date=timezone.now().date()
                    ).count(),
                    'staff_users': User.objects.filter(is_staff=True).count(),
                }
            })
        
        return super().index(request, extra_context)


# Create custom admin site instance
hawwa_admin_site = HawwaAdminSite(name='hawwa_admin')

# Register models with custom admin site
from django.contrib.auth.models import Group, Permission
hawwa_admin_site.register(User, admin.site._registry[User].__class__)
hawwa_admin_site.register(Group)
hawwa_admin_site.register(Permission)