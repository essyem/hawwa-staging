from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

class VendorProfile(models.Model):
    """Extended profile for vendors/service providers"""
    
    VENDOR_STATUS_CHOICES = (
        ('pending', _('Pending Approval')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('inactive', _('Inactive')),
    )
    
    BUSINESS_TYPE_CHOICES = (
        ('individual', _('Individual')),
        ('small_business', _('Small Business')),
        ('corporation', _('Corporation')),
        ('ngo', _('NGO/Non-Profit')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
    )
    
    # Business Information
    business_name = models.CharField(_('Business Name'), max_length=200)
    business_type = models.CharField(_('Business Type'), max_length=20, choices=BUSINESS_TYPE_CHOICES)
    business_license = models.CharField(_('Business License'), max_length=100, blank=True)
    tax_id = models.CharField(_('Tax ID'), max_length=50, blank=True)
    
    # Contact & Location
    business_phone = models.CharField(_('Business Phone'), max_length=20)
    business_email = models.EmailField(_('Business Email'))
    website = models.URLField(_('Website'), blank=True)
    
    # Service Areas
    service_areas = models.TextField(_('Service Areas'), help_text=_('Areas where you provide services'))
    
    # Status & Verification
    status = models.CharField(_('Status'), max_length=20, choices=VENDOR_STATUS_CHOICES, default='pending')
    verified = models.BooleanField(_('Verified'), default=False)
    verification_date = models.DateTimeField(_('Verification Date'), blank=True, null=True)
    
    # Ratings & Performance
    average_rating = models.DecimalField(_('Average Rating'), max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(_('Total Reviews'), default=0)
    total_bookings = models.PositiveIntegerField(_('Total Bookings'), default=0)
    completed_bookings = models.PositiveIntegerField(_('Completed Bookings'), default=0)
    
    # Financial
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, decimal_places=2, default=15.00)
    total_earnings = models.DecimalField(_('Total Earnings'), max_digits=12, decimal_places=2, default=0)
    
    # Timestamps
    joined_date = models.DateTimeField(_('Joined Date'), auto_now_add=True)
    last_active = models.DateTimeField(_('Last Active'), auto_now=True)
    
    # Settings
    auto_accept_bookings = models.BooleanField(_('Auto Accept Bookings'), default=False)
    notification_email = models.BooleanField(_('Email Notifications'), default=True)
    notification_sms = models.BooleanField(_('SMS Notifications'), default=True)
    
    class Meta:
        verbose_name = _('Vendor Profile')
        verbose_name_plural = _('Vendor Profiles')
    
    def __str__(self):
        return f"{self.business_name} ({self.user.get_full_name()})"
    
    def get_absolute_url(self):
        return reverse('vendors:profile', kwargs={'pk': self.pk})
    
    def get_completion_rate(self):
        """Calculate booking completion rate"""
        if self.total_bookings == 0:
            return 0
        return (self.completed_bookings / self.total_bookings) * 100
    
    def get_response_time(self):
        """Calculate average response time for bookings"""
        # This would be calculated from booking response data
        return "< 2 hours"  # Placeholder
    
    def update_stats(self):
        """Update vendor statistics from bookings"""
        from bookings.models import Booking
        
        vendor_bookings = Booking.objects.filter(service__in=self.user.services.all())
        self.total_bookings = vendor_bookings.count()
        self.completed_bookings = vendor_bookings.filter(status='completed').count()
        
        # Calculate average rating from reviews
        from services.models import ServiceReview
        reviews = ServiceReview.objects.filter(service__in=self.user.services.all())
        if reviews.exists():
            self.average_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
            self.total_reviews = reviews.count()
        
        self.save()


class VendorDocument(models.Model):
    """Documents uploaded by vendors for verification"""
    
    DOCUMENT_TYPE_CHOICES = (
        ('license', _('Business License')),
        ('insurance', _('Insurance Certificate')),
        ('certification', _('Professional Certification')),
        ('tax_certificate', _('Tax Certificate')),
        ('identity', _('Identity Document')),
        ('other', _('Other')),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    )
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(_('Document Type'), max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(_('Title'), max_length=200)
    document_file = models.FileField(_('Document File'), upload_to='vendor_documents/')
    description = models.TextField(_('Description'), blank=True)
    
    status = models.CharField(_('Status'), max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    uploaded_date = models.DateTimeField(_('Uploaded Date'), auto_now_add=True)
    verified_date = models.DateTimeField(_('Verified Date'), blank=True, null=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    
    expiry_date = models.DateField(_('Expiry Date'), blank=True, null=True)
    notes = models.TextField(_('Admin Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Vendor Document')
        verbose_name_plural = _('Vendor Documents')
        ordering = ['-uploaded_date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.get_document_type_display()}"
    
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class VendorAvailability(models.Model):
    """Vendor availability schedule"""
    
    DAY_CHOICES = (
        ('monday', _('Monday')),
        ('tuesday', _('Tuesday')),
        ('wednesday', _('Wednesday')),
        ('thursday', _('Thursday')),
        ('friday', _('Friday')),
        ('saturday', _('Saturday')),
        ('sunday', _('Sunday')),
    )
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    day_of_week = models.CharField(_('Day of Week'), max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    is_available = models.BooleanField(_('Available'), default=True)
    
    class Meta:
        verbose_name = _('Vendor Availability')
        verbose_name_plural = _('Vendor Availability')
        unique_together = ['vendor', 'day_of_week']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.vendor.business_name} - {self.get_day_of_week_display()} ({status})"


class VendorBlackoutDate(models.Model):
    """Specific dates when vendor is not available"""
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='blackout_dates'
    )
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    reason = models.CharField(_('Reason'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        verbose_name = _('Vendor Blackout Date')
        verbose_name_plural = _('Vendor Blackout Dates')
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.start_date} to {self.end_date}"


class VendorPayment(models.Model):
    """Payment records for vendors"""
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    
    PAYMENT_TYPE_CHOICES = (
        ('commission', _('Commission Payment')),
        ('bonus', _('Performance Bonus')),
        ('refund', _('Refund')),
        ('adjustment', _('Adjustment')),
    )
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    payment_type = models.CharField(_('Payment Type'), max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='QAR')
    
    # Period this payment covers
    period_start = models.DateField(_('Period Start'))
    period_end = models.DateField(_('Period End'))
    
    # Booking references
    booking_count = models.PositiveIntegerField(_('Bookings Count'), default=0)
    gross_amount = models.DecimalField(_('Gross Amount'), max_digits=12, decimal_places=2, default=0)
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, decimal_places=2)
    
    status = models.CharField(_('Status'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(_('Payment Date'), blank=True, null=True)
    reference_number = models.CharField(_('Reference Number'), max_length=100, blank=True)
    
    notes = models.TextField(_('Notes'), blank=True)
    created_date = models.DateTimeField(_('Created Date'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vendor Payment')
        verbose_name_plural = _('Vendor Payments')
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.amount} {self.currency} ({self.status})"


class VendorAnalytics(models.Model):
    """Analytics data for vendors"""
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Time period
    date = models.DateField(_('Date'))
    
    # Booking metrics
    bookings_received = models.PositiveIntegerField(_('Bookings Received'), default=0)
    bookings_accepted = models.PositiveIntegerField(_('Bookings Accepted'), default=0)
    bookings_completed = models.PositiveIntegerField(_('Bookings Completed'), default=0)
    bookings_cancelled = models.PositiveIntegerField(_('Bookings Cancelled'), default=0)
    
    # Financial metrics
    revenue = models.DecimalField(_('Revenue'), max_digits=10, decimal_places=2, default=0)
    commission_paid = models.DecimalField(_('Commission Paid'), max_digits=10, decimal_places=2, default=0)
    
    # Performance metrics
    average_rating = models.DecimalField(_('Average Rating'), max_digits=3, decimal_places=2, default=0)
    response_time_minutes = models.PositiveIntegerField(_('Avg Response Time (min)'), default=0)
    
    class Meta:
        verbose_name = _('Vendor Analytics')
        verbose_name_plural = _('Vendor Analytics')
        unique_together = ['vendor', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.date}"
