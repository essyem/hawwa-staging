from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    DocpoolDepartment, DocpoolDocumentType, DocpoolDocumentBorder,
    DocpoolReferenceNumber, DocpoolDocumentCategory, DocpoolDocumentSubCategory,
    DocpoolDocument, DocpoolSearchLog, DocpoolDocumentAccess
)

# Custom admin form for documents with validation
class DocpoolDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = DocpoolDocument
        fields = '__all__'

    def clean(self):
        # Delegate to model clean() so business validation is shared
        cleaned = super().clean()
        try:
            self.instance = self.instance or self.Meta.model()
            for k, v in cleaned.items():
                setattr(self.instance, k, v)
            self.instance.full_clean()
        except forms.ValidationError as e:
            # Convert model ValidationError into form validation errors
            raise
        return cleaned

# Department Admin
@admin.register(DocpoolDepartment)
class DocpoolDepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'document_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count(self, obj):
        count = obj.documents.count()
        if count > 0:
            url = reverse('admin:docpool_docpooldocument_changelist') + f'?department__id__exact={obj.id}'
            return format_html('<a href="{}">{} documents</a>', url, count)
        return '0 documents'
    document_count.short_description = 'Documents'

# Document Type Admin
@admin.register(DocpoolDocumentType)
class DocpoolDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'document_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count(self, obj):
        count = obj.documents.count()
        if count > 0:
            url = reverse('admin:docpool_docpooldocument_changelist') + f'?document_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} documents</a>', url, count)
        return '0 documents'
    document_count.short_description = 'Documents'

# Document Border Admin
@admin.register(DocpoolDocumentBorder)
class DocpoolDocumentBorderAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'document_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count(self, obj):
        count = obj.documents.count()
        if count > 0:
            url = reverse('admin:docpool_docpooldocument_changelist') + f'?border__id__exact={obj.id}'
            return format_html('<a href="{}">{} documents</a>', url, count)
        return '0 documents'
    document_count.short_description = 'Documents'

# Reference Number Admin
@admin.register(DocpoolReferenceNumber)
class DocpoolReferenceNumberAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'department', 'document_type', 'year', 'month', 'sequence', 'is_used', 'created_at']
    list_filter = ['year', 'month', 'department', 'document_type', 'is_used', 'created_at']
    search_fields = ['reference_number']
    readonly_fields = ['reference_number', 'sequence', 'created_at', 'created_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Reference Information', {
            'fields': ('reference_number', 'department', 'document_type')
        }),
        ('Time Information', {
            'fields': ('year', 'month', 'sequence')
        }),
        ('Status', {
            'fields': ('is_used',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual addition - references should be auto-generated
        return False

# Legacy Category Admin (for backward compatibility)
@admin.register(DocpoolDocumentCategory)
class DocpoolDocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_count', 'subcategory_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'
    
    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Sub-categories'

# Legacy Sub-Category Admin (for backward compatibility)
@admin.register(DocpoolDocumentSubCategory)
class DocpoolDocumentSubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'document_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['category__name', 'name']
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'

# Main Document Admin
@admin.register(DocpoolDocument)
class DocpoolDocumentAdmin(admin.ModelAdmin):
    form = DocpoolDocumentAdminForm
    list_display = ['title', 'reference_display', 'year', 'month', 'department', 'document_type', 'border', 'access_level', 'file_size_display', 'uploaded_by', 'uploaded_at']
    list_filter = ['year', 'month', 'department', 'document_type', 'border', 'access_level', 'is_active', 'is_confidential', 'uploaded_at']
    search_fields = ['title', 'description', 'keywords', 'reference_number__reference_number']
    readonly_fields = ['reference_number', 'file_size', 'file_type', 'uploaded_at', 'updated_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('file', 'title', 'description', 'keywords')
        }),
        ('Classification', {
            'fields': ('year', 'month', 'department', 'document_type', 'border')
        }),
        ('Legacy Classification', {
            'fields': ('category', 'subcategory'),
            'classes': ('collapse',),
            'description': 'Legacy fields for backward compatibility'
        }),
        ('Access Control', {
            'fields': ('access_level', 'is_confidential', 'is_active')
        }),
        ('System Information', {
            'fields': ('reference_number', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reference_display(self, obj):
        if obj.reference_number:
            return format_html('<span style="font-family: monospace; font-weight: bold;">{}</span>', 
                             obj.reference_number.reference_number)
        return '-'
    reference_display.short_description = 'Reference'
    
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'department', 'document_type', 'border', 'category', 'subcategory', 
            'reference_number', 'uploaded_by'
        )

# Search Log Admin (for analytics)
@admin.register(DocpoolSearchLog)
class DocpoolSearchLogAdmin(admin.ModelAdmin):
    list_display = ['query_display', 'results_count', 'user', 'timestamp', 'filters_summary']
    list_filter = ['timestamp', 'user', 'results_count']
    search_fields = ['query', 'user__username']
    readonly_fields = ['query', 'results_count', 'user', 'ip_address', 'timestamp', 
                      'department_filter', 'document_type_filter', 'year_filter', 'border_filter']
    ordering = ['-timestamp']
    
    def query_display(self, obj):
        query = obj.query
        if len(query) > 50:
            return f"{query[:47]}..."
        return query
    query_display.short_description = 'Search Query'
    
    def filters_summary(self, obj):
        filters = []
        if obj.department_filter:
            filters.append(f"Dept: {obj.department_filter}")
        if obj.document_type_filter:
            filters.append(f"Type: {obj.document_type_filter}")
        if obj.year_filter:
            filters.append(f"Year: {obj.year_filter}")
        if obj.border_filter:
            filters.append(f"Border: {obj.border_filter}")
        return " | ".join(filters) if filters else "No filters"
    filters_summary.short_description = 'Filters Applied'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Document Access Log Admin (for audit)
@admin.register(DocpoolDocumentAccess)
class DocpoolDocumentAccessAdmin(admin.ModelAdmin):
    list_display = ['document_title', 'access_type', 'user', 'ip_address', 'timestamp']
    list_filter = ['access_type', 'timestamp', 'user']
    search_fields = ['document__title', 'user__username', 'ip_address']
    readonly_fields = ['document', 'user', 'ip_address', 'access_type', 'timestamp', 'user_agent']
    ordering = ['-timestamp']
    
    def document_title(self, obj):
        return obj.document.title
    document_title.short_description = 'Document'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'user')
