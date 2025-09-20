from django.contrib import admin
from .models import ChangeRequest, Incident, Lead
from .models import Role, RoleAssignment, Comment, Activity
from .models import Comment, Activity
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import admin, messages
from django import forms
from django.contrib.auth import get_user_model


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'reporter', 'assignee', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description')
    actions = ['assign_to_user_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin-dashboard/', self.admin_site.admin_view(self.dashboard_view), name='change_management_dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # simple counts by status/priority
        qs = ChangeRequest.objects.all()
        status_counts = qs.values('status').order_by().annotate(count=forms.models.Count('id'))
        priority_counts = qs.values('priority').order_by().annotate(count=forms.models.Count('id'))
        return render(request, 'change_management/admin/dashboard.html', {'status_counts': status_counts, 'priority_counts': priority_counts})

    def assign_to_user_action(self, request, queryset):
        """Admin action that prompts for a user id and assigns selected CRs to that user."""
        User = get_user_model()
        if 'apply' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(pk=user_id)
            except Exception:
                self.message_user(request, 'User not found', level=messages.ERROR)
                return
            updated = queryset.update(assignee=user)
            self.message_user(request, f'Assigned {updated} change request(s) to {user.email}')
            return None

        # Display intermediate page
        return render(request, 'change_management/admin/assign_confirmation.html', context={'objects': queryset})


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'severity', 'reporter', 'resolved', 'created_at')
    list_filter = ('severity', 'resolved')
    search_fields = ('title', 'details')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'owner', 'created_at')
    search_fields = ('name', 'email', 'phone')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'created_at')
    search_fields = ('user__email', 'role__name')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'text', 'created_at')
    search_fields = ('text',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'actor', 'verb', 'target', 'created_at')
    search_fields = ('verb', 'target')
