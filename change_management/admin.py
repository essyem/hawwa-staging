from django.contrib import admin
from .models import ChangeRequest, Incident, Lead


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'reporter', 'assignee', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description')


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'severity', 'reporter', 'resolved', 'created_at')
    list_filter = ('severity', 'resolved')
    search_fields = ('title', 'details')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'owner', 'created_at')
    search_fields = ('name', 'email', 'phone')
