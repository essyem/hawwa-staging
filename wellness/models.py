from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from accounts.models import User

class WellnessCategory(models.Model):
    """Category for wellness programs (e.g., Meditation, Yoga, Mental Health)"""
    name = models.CharField(_("Category Name"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=120)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to='wellness/categories/', blank=True, null=True)
    icon = models.CharField(_("Icon Class"), max_length=50, blank=True, help_text=_("Font Awesome icon class"))
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Wellness Category")
        verbose_name_plural = _("Wellness Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse("wellness:category_detail", kwargs={"slug": self.slug})

class WellnessProgram(models.Model):
    """Wellness program model (e.g., specific meditation class, yoga session)"""
    PROGRAM_STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('coming_soon', _('Coming Soon')),
    ]
    
    name = models.CharField(_("Program Name"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True, max_length=220)
    category = models.ForeignKey(
        WellnessCategory, 
        on_delete=models.CASCADE, 
        related_name='programs',
        verbose_name=_("Category")
    )
    short_description = models.CharField(_("Short Description"), max_length=200)
    description = models.TextField(_("Description"))
    benefits = models.TextField(_("Benefits"), blank=True)
    duration = models.IntegerField(_("Duration (minutes)"), default=60)
    image = models.ImageField(_("Image"), upload_to='wellness/programs/')
    video_url = models.URLField(_("Video URL"), blank=True, null=True, help_text=_("YouTube or Vimeo URL"))
    status = models.CharField(_("Status"), max_length=20, choices=PROGRAM_STATUS_CHOICES, default='active')
    featured = models.BooleanField(_("Featured"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    # Provider information
    provider = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='wellness_programs',
        limit_choices_to={'user_type__in': ['WELLNESS', 'MEDITATION', 'MENTAL_HEALTH']},
        verbose_name=_("Provider")
    )
    
    class Meta:
        verbose_name = _("Wellness Program")
        verbose_name_plural = _("Wellness Programs")
        ordering = ['-featured', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse("wellness:program_detail", kwargs={"slug": self.slug})

class WellnessSession(models.Model):
    """Individual wellness session instance"""
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    program = models.ForeignKey(
        WellnessProgram, 
        on_delete=models.CASCADE, 
        related_name='sessions',
        verbose_name=_("Program")
    )
    title = models.CharField(_("Session Title"), max_length=200)
    date = models.DateField(_("Session Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    location = models.CharField(_("Location"), max_length=255, blank=True)
    online_link = models.URLField(_("Online Meeting Link"), blank=True, null=True)
    is_online = models.BooleanField(_("Online Session"), default=False)
    max_participants = models.IntegerField(_("Maximum Participants"), default=10)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Wellness Session")
        verbose_name_plural = _("Wellness Sessions")
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.program.name} - {self.date} {self.start_time}"
    
    def get_absolute_url(self):
        return reverse("wellness:session_detail", kwargs={"pk": self.pk})

class WellnessEnrollment(models.Model):
    """User enrollment in a wellness program"""
    STATUS_CHOICES = [
        ('enrolled', _('Enrolled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='wellness_enrollments',
        verbose_name=_("User")
    )
    program = models.ForeignKey(
        WellnessProgram, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name=_("Program")
    )
    session = models.ForeignKey(
        WellnessSession, 
        on_delete=models.CASCADE, 
        related_name='participants',
        verbose_name=_("Session"),
        null=True,
        blank=True
    )
    enrolled_at = models.DateTimeField(_("Enrolled At"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='enrolled')
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Wellness Enrollment")
        verbose_name_plural = _("Wellness Enrollments")
        unique_together = ['user', 'session']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.program.name}"

class WellnessReview(models.Model):
    """User reviews for wellness programs"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='wellness_reviews',
        verbose_name=_("User")
    )
    program = models.ForeignKey(
        WellnessProgram, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name=_("Program")
    )
    rating = models.IntegerField(_("Rating"), choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(_("Comment"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Wellness Review")
        verbose_name_plural = _("Wellness Reviews")
        unique_together = ['user', 'program']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.program.name} - {self.rating}★"
