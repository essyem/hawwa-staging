from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime

User = get_user_model()

class DocpoolDepartment(models.Model):
    """Department model for document classification (separate from HRMS departments)"""
    DEPARTMENT_CHOICES = [
        ('HRD', 'Human Resources Department'),
        ('FIN', 'Finance Department'),
        ('OPR', 'Operations Department'),
        ('TEC', 'Technical Department'),
        ('MKT', 'Marketing Department'),
        ('LEG', 'Legal Department'),
        ('ADM', 'Administration Department'),
        ('ITD', 'IT Department'),
        ('PRJ', 'Project Management'),
        ('QUA', 'Quality Assurance'),
        ('WEL', 'Wellness Department'),
        ('VEN', 'Vendor Management'),
        ('BOO', 'Booking Management'),
        ('PAY', 'Payment Processing'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Document Department'
        verbose_name_plural = 'Document Departments'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class DocpoolDocumentType(models.Model):
    """Document type for classification"""
    TYPE_CHOICES = [
        ('MOI', 'Ministry of Interior'),
        ('MOL', 'Ministry of Labour'),
        ('MOF', 'Ministry of Finance'),
        ('MOH', 'Ministry of Health'),
        ('CRA', 'Commercial Registration Authority'),
        ('TAX', 'Tax Authority'),
        ('CUS', 'Customs Authority'),
        ('BAN', 'Banking Documents'),
        ('LEG', 'Legal Documents'),
        ('CON', 'Contracts'),
        ('RPT', 'Reports'),
        ('CER', 'Certificates'),
        ('LIC', 'Licenses'),
        ('PER', 'Permits'),
        ('INV', 'Invoices'),
        ('REC', 'Receipts'),
        ('COR', 'Correspondence'),
        ('POL', 'Policies'),
        ('PRO', 'Procedures'),
        ('MEM', 'Memorandums'),
        ('EMP', 'Employee Documents'),
        ('VND', 'Vendor Documents'),
        ('WEL', 'Wellness Documents'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class DocpoolDocumentBorder(models.Model):
    """Document border classification"""
    BORDER_CHOICES = [
        ('INT', 'Internal'),
        ('EXT', 'External'),
        ('GOV', 'Government'),
        ('PRI', 'Private'),
        ('URG', 'Urgent'),
        ('CON', 'Confidential'),
        ('PUB', 'Public'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Document Border'
        verbose_name_plural = 'Document Borders'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class DocpoolReferenceNumber(models.Model):
    """Model to track generated reference numbers"""
    reference_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(DocpoolDepartment, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocpoolDocumentType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    sequence = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Reference Number'
        verbose_name_plural = 'Reference Numbers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['year', 'month', 'department', 'document_type']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        return self.reference_number
    
    @classmethod
    def generate_reference(cls, department, document_type, user=None):
        """Generate a new reference number for Hawwa system"""
        now = timezone.now()
        year = now.year
        month = now.month
        
        # Get the last sequence number for this department/type/year/month
        last_ref = cls.objects.filter(
            department=department,
            document_type=document_type,
            year=year,
            month=month
        ).order_by('-sequence').first()
        
        if last_ref:
            sequence = last_ref.sequence + 1
        else:
            sequence = 1001  # Start from 1001
        
        # Format: HAWWA/[Dept]/[Type]/[YearMonth][Sequence]
        year_short = str(year)[-2:]  # Last 2 digits of year
        month_str = f"{month:02d}"   # 2-digit month
        sequence_str = f"{sequence:04d}"  # 4-digit sequence
        
        reference = f"HAWWA/{department.code}/{document_type.code}/{year_short}{month_str}{sequence_str}"
        
        # Create the reference number record
        ref_obj = cls.objects.create(
            reference_number=reference,
            department=department,
            document_type=document_type,
            year=year,
            month=month,
            sequence=sequence,
            created_by=user
        )
        
        return ref_obj


class DocpoolDocumentCategory(models.Model):
    """Legacy document category for backward compatibility"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class DocpoolDocumentSubCategory(models.Model):
    """Legacy document subcategory for backward compatibility"""
    category = models.ForeignKey(
        DocpoolDocumentCategory,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document Sub-Category'
        verbose_name_plural = 'Document Sub-Categories'
        unique_together = ('category', 'name')
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class DocpoolDocument(models.Model):
    """Main document model for the document pool system"""
    file = models.FileField(upload_to='docpool/documents/%Y/%m/%d/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Core document metadata
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(
        choices=[(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        null=True,
        blank=True
    )
    
    # Legacy fields (for backward compatibility)
    category = models.ForeignKey(
        DocpoolDocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents',
        blank=True
    )
    subcategory = models.ForeignKey(
        DocpoolDocumentSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents',
        blank=True
    )
    
    # New classification fields
    border = models.ForeignKey(
        DocpoolDocumentBorder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    document_type = models.ForeignKey(
        DocpoolDocumentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    department = models.ForeignKey(
        DocpoolDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    # Auto-generated reference number
    reference_number = models.ForeignKey(
        DocpoolReferenceNumber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    # File metadata
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    
    # Tracking and audit
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='docpool_uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status and access
    is_active = models.BooleanField(default=True)
    is_confidential = models.BooleanField(default=False)
    access_level = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('confidential', 'Confidential'),
    ], default='internal')
    
    # Search and indexing
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for searching")
    
    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['year']),
            models.Index(fields=['month']),
            models.Index(fields=['border']),
            models.Index(fields=['document_type']),
            models.Index(fields=['department']),
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['access_level']),
            models.Index(fields=['is_active']),
            models.Index(fields=['uploaded_at']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Set file metadata
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower() if '.' in self.file.name else 'unknown'
        
        # Set year and month if not provided
        if not self.year:
            self.year = timezone.now().year
        if not self.month:
            self.month = timezone.now().month
        
        # Ensure model-level validation before saving
        try:
            self.full_clean()
        except ValidationError:
            # Let the caller handle form-level errors; re-raise so failures
            # aren't silently swallowed when save() is invoked directly.
            raise
            
        # Auto-generate reference number if not already assigned and all required fields are present
        if not self.reference_number and self.department and self.document_type:
            self.reference_number = DocpoolReferenceNumber.generate_reference(
                self.department, 
                self.document_type, 
                self.uploaded_by
            )
            # Mark the reference as used
            self.reference_number.is_used = True
            self.reference_number.save()
        
        super().save(*args, **kwargs)

    def clean(self):
        """Model-level validation: business rules"""
        # Business rule: Operations department cannot create External bordered documents
        if self.department and self.border:
            d_code = (self.department.code or '').upper()
            b_code = (self.border.code or '').upper()
            if d_code.startswith('OPR') and b_code == 'EXT':
                raise ValidationError({
                    'border': 'Operations department cannot create External (EXT) bordered documents.'
                })
        
        # Ensure confidential documents have restricted access
        if self.is_confidential and self.access_level not in ['restricted', 'confidential']:
            raise ValidationError({
                'access_level': 'Confidential documents must have restricted or confidential access level.'
            })
    
    @property
    def file_size_display(self):
        """Human readable file size"""
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    @property
    def can_be_public(self):
        """Check if document can be made public based on classification"""
        if self.is_confidential:
            return False
        if self.border and self.border.code in ['CON', 'GOV']:
            return False
        return True
    
    def get_absolute_url(self):
        """Get URL for document detail view"""
        from django.urls import reverse
        return reverse('docpool:document_detail', kwargs={'pk': self.pk})


class DocpoolSearchLog(models.Model):
    """Track document searches for analytics"""
    query = models.CharField(max_length=500)
    results_count = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Search parameters
    department_filter = models.CharField(max_length=10, blank=True)
    document_type_filter = models.CharField(max_length=10, blank=True)
    year_filter = models.PositiveIntegerField(null=True, blank=True)
    border_filter = models.CharField(max_length=10, blank=True)
    
    class Meta:
        verbose_name = 'Search Log'
        verbose_name_plural = 'Search Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        return f"Search: {self.query[:50]}{'...' if len(self.query) > 50 else ''}"


class DocpoolDocumentAccess(models.Model):
    """Track document access for audit purposes"""
    document = models.ForeignKey(DocpoolDocument, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('download', 'Download'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['access_type']),
        ]
    
    def __str__(self):
        return f"{self.access_type} - {self.document.title} by {self.user}"
