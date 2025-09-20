from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from datetime import timedelta

class ServiceCategory(models.Model):
    """Model for categorizing services."""
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("Icon Class"), max_length=50, help_text=_("Font Awesome icon class (e.g., 'fa-spa')"), blank=True)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    
    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(models.Model):
    """Base model for all services offered."""
    AVAILABILITY_STATUS = (
        ('available', _('Available')),
        ('unavailable', _('Unavailable')),
        ('limited', _('Limited Availability')),
    )
    
    name = models.CharField(_("Service Name"), max_length=200)
    description = models.TextField(_("Description"))
    short_description = models.CharField(_("Short Description"), max_length=200, blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    # Optional cost field to record the supplier/cost price for COGS calculations
    cost = models.DecimalField(_("Cost"), max_digits=10, decimal_places=2, default=0)
    duration = models.DurationField(_("Duration"), help_text=_("Expected duration of the service"))
    category = models.ForeignKey(ServiceCategory, related_name="services", on_delete=models.CASCADE)
    vendor_profile = models.ForeignKey(
        'vendors.VendorProfile', 
        related_name="services", 
        on_delete=models.CASCADE,
        verbose_name=_("Vendor"),
        help_text=_("The vendor/service provider offering this service"),
        null=True,
        blank=True
    )
    image = models.ImageField(_("Service Image"), upload_to='services/', blank=True, null=True)
    status = models.CharField(_("Availability Status"), max_length=20, choices=AVAILABILITY_STATUS, default='available')
    featured = models.BooleanField(_("Featured Service"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True)
    
    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Allow tests and fixtures to set duration as a string like '01:00:00',
        # or as an integer/float number of seconds. Django's DurationField
        # expects a datetime.timedelta; coerce if necessary.
        if isinstance(self.duration, str):
            try:
                parts = self.duration.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    self.duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                elif len(parts) == 2:
                    minutes, seconds = map(int, parts)
                    self.duration = timedelta(minutes=minutes, seconds=seconds)
            except Exception:
                # leave as-is and let Django validation raise if invalid
                pass
        elif isinstance(self.duration, (int, float)):
            # Treat numeric durations as seconds
            try:
                self.duration = timedelta(seconds=int(self.duration))
            except Exception:
                pass

        if not self.short_description and self.description:
            # Create a short description from the full description if not provided
            self.short_description = self.description[:197] + "..." if len(self.description) > 200 else self.description
            
        super().save(*args, **kwargs)


class AccommodationService(Service):
    """Model for accommodation services like retreat stays."""
    location = models.CharField(_("Location"), max_length=255)
    address = models.TextField(_("Address"))
    capacity = models.PositiveIntegerField(_("Capacity"), help_text=_("Maximum number of guests"))
    amenities = models.TextField(_("Amenities"), help_text=_("List of amenities available"))
    room_type = models.CharField(_("Room Type"), max_length=100)
    check_in_time = models.TimeField(_("Check-in Time"))
    check_out_time = models.TimeField(_("Check-out Time"))
    
    class Meta:
        verbose_name = _("Accommodation Service")
        verbose_name_plural = _("Accommodation Services")


class HomeCareService(Service):
    """Model for home care services."""
    service_area = models.CharField(_("Service Area"), max_length=255, help_text=_("Geographic areas where this service is available"))
    min_hours = models.PositiveIntegerField(_("Minimum Hours"), default=2, help_text=_("Minimum booking hours"))
    
    class Meta:
        verbose_name = _("Home Care Service")
        verbose_name_plural = _("Home Care Services")


class WellnessService(Service):
    """Model for wellness services like massage, meditation, etc."""
    service_type = models.CharField(_("Service Type"), max_length=100, help_text=_("E.g., Massage, Meditation, Counseling"))
    is_virtual = models.BooleanField(_("Virtual Service"), default=False, help_text=_("Whether this service can be provided virtually"))
    
    class Meta:
        verbose_name = _("Wellness Service")
        verbose_name_plural = _("Wellness Services")


class NutritionService(Service):
    """Model for nutritional services and meal plans."""
    dietary_options = models.TextField(_("Dietary Options"), help_text=_("Available dietary options (e.g., vegetarian, vegan)"))
    is_customizable = models.BooleanField(_("Customizable"), default=True)
    preparation_time = models.DurationField(_("Preparation Time"), help_text=_("Time needed to prepare"))
    delivery_available = models.BooleanField(_("Delivery Available"), default=True)
    
    class Meta:
        verbose_name = _("Nutrition Service")
        verbose_name_plural = _("Nutrition Services")


class ServiceReview(models.Model):
    """Model for service reviews and ratings."""
    service = models.ForeignKey(Service, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="service_reviews", on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(_("Rating"), validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(_("Comment"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    is_public = models.BooleanField(_("Public Review"), default=True)
    
    class Meta:
        verbose_name = _("Service Review")
        verbose_name_plural = _("Service Reviews")
        ordering = ['-created_at']
        # Ensure one review per user per service
        unique_together = ['service', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.service.name}: {self.rating}/5"


class ServiceImage(models.Model):
    """Model for additional service images."""
    service = models.ForeignKey(Service, related_name="additional_images", on_delete=models.CASCADE)
    image = models.ImageField(_("Image"), upload_to='services/gallery/')
    caption = models.CharField(_("Caption"), max_length=255, blank=True)
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)
    
    class Meta:
        verbose_name = _("Service Image")
        verbose_name_plural = _("Service Images")
        ordering = ['display_order']
    
    def __str__(self):
        return f"Image for {self.service.name} - {self.id}"
