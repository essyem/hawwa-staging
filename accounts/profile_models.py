from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User

class MotherProfile(models.Model):
    """Profile model for users of type Mother."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mother_profile')
    
    # Pregnancy and birth details
    due_date = models.DateField(_('Due Date'), blank=True, null=True)
    birth_date = models.DateField(_('Birth Date'), blank=True, null=True)
    baby_name = models.CharField(_('Baby Name'), max_length=100, blank=True, null=True)
    baby_gender = models.CharField(_('Baby Gender'), max_length=10, blank=True, null=True)
    
    # Medical information
    blood_type = models.CharField(_('Blood Type'), max_length=10, blank=True, null=True)
    allergies = models.TextField(_('Allergies'), blank=True, null=True)
    medical_conditions = models.TextField(_('Medical Conditions'), blank=True, null=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(_('Emergency Contact Name'), max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(_('Emergency Contact Phone'), max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(_('Emergency Contact Relationship'), max_length=50, blank=True, null=True)
    
    # Preferences
    dietary_preferences = models.TextField(_('Dietary Preferences'), blank=True, null=True)
    special_requirements = models.TextField(_('Special Requirements'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Mother Profile')
        verbose_name_plural = _('Mother Profiles')
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"

class AccommodationProviderProfile(models.Model):
    """Profile model for users of type Accommodation Provider."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accommodation_profile')
    
    # Business details
    business_name = models.CharField(_('Business Name'), max_length=200)
    business_registration_number = models.CharField(_('Business Registration Number'), max_length=50, blank=True, null=True)
    years_in_business = models.PositiveIntegerField(_('Years in Business'), default=0)
    
    # Accommodation details
    property_type = models.CharField(_('Property Type'), max_length=100)
    number_of_rooms = models.PositiveIntegerField(_('Number of Rooms'), default=0)
    amenities = models.TextField(_('Amenities'), blank=True, null=True)
    
    # Location
    location_description = models.TextField(_('Location Description'), blank=True, null=True)
    
    # Verification and certification
    is_verified = models.BooleanField(_('Verified'), default=False)
    certifications = models.TextField(_('Certifications'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Accommodation Provider Profile')
        verbose_name_plural = _('Accommodation Provider Profiles')
    
    def __str__(self):
        return f"{self.business_name} - {self.user.get_full_name()}"

class CaretakerProviderProfile(models.Model):
    """Profile model for users of type Caretaker Provider."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='caretaker_profile')
    
    # Professional details
    years_of_experience = models.PositiveIntegerField(_('Years of Experience'), default=0)
    specializations = models.TextField(_('Specializations'), blank=True, null=True)
    
    # Education and certification
    qualifications = models.TextField(_('Qualifications'), blank=True, null=True)
    certifications = models.TextField(_('Certifications'), blank=True, null=True)
    license_number = models.CharField(_('License Number'), max_length=50, blank=True, null=True)
    
    # Services offered
    services_offered = models.TextField(_('Services Offered'), blank=True, null=True)
    
    # Availability
    availability = models.TextField(_('Availability'), blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    background_check_passed = models.BooleanField(_('Background Check Passed'), default=False)
    
    class Meta:
        verbose_name = _('Caretaker Provider Profile')
        verbose_name_plural = _('Caretaker Provider Profiles')
    
    def __str__(self):
        return f"Caretaker: {self.user.get_full_name()}"

class WellnessProviderProfile(models.Model):
    """Profile model for users of type Wellness Service Provider."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wellness_profile')
    
    # Professional details
    business_name = models.CharField(_('Business Name'), max_length=200, blank=True, null=True)
    service_type = models.CharField(_('Service Type'), max_length=100)
    years_of_experience = models.PositiveIntegerField(_('Years of Experience'), default=0)
    
    # Services
    services_offered = models.TextField(_('Services Offered'), blank=True, null=True)
    specializations = models.TextField(_('Specializations'), blank=True, null=True)
    
    # Qualifications
    qualifications = models.TextField(_('Qualifications'), blank=True, null=True)
    certifications = models.TextField(_('Certifications'), blank=True, null=True)
    license_number = models.CharField(_('License Number'), max_length=50, blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    
    class Meta:
        verbose_name = _('Wellness Provider Profile')
        verbose_name_plural = _('Wellness Provider Profiles')
    
    def __str__(self):
        business = self.business_name or self.user.get_full_name()
        return f"{business} - {self.service_type}"

class MeditationConsultantProfile(models.Model):
    """Profile model for users of type Meditation Consultant."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meditation_profile')
    
    # Professional details
    years_of_experience = models.PositiveIntegerField(_('Years of Experience'), default=0)
    practice_type = models.CharField(_('Practice Type'), max_length=100)
    
    # Qualifications
    qualifications = models.TextField(_('Qualifications'), blank=True, null=True)
    certifications = models.TextField(_('Certifications'), blank=True, null=True)
    
    # Services
    services_offered = models.TextField(_('Services Offered'), blank=True, null=True)
    specializations = models.TextField(_('Specializations'), blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    
    class Meta:
        verbose_name = _('Meditation Consultant Profile')
        verbose_name_plural = _('Meditation Consultant Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.practice_type}"

class MentalHealthConsultantProfile(models.Model):
    """Profile model for users of type Mental Health Consultant."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mental_health_profile')
    
    # Professional details
    title = models.CharField(_('Professional Title'), max_length=100)
    years_of_experience = models.PositiveIntegerField(_('Years of Experience'), default=0)
    areas_of_expertise = models.TextField(_('Areas of Expertise'), blank=True, null=True)
    
    # Qualifications
    education = models.TextField(_('Education'), blank=True, null=True)
    qualifications = models.TextField(_('Qualifications'), blank=True, null=True)
    license_number = models.CharField(_('License Number'), max_length=50, blank=True, null=True)
    
    # Services
    services_offered = models.TextField(_('Services Offered'), blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    
    class Meta:
        verbose_name = _('Mental Health Consultant Profile')
        verbose_name_plural = _('Mental Health Consultant Profiles')
    
    def __str__(self):
        return f"{self.title} {self.user.get_full_name()}"

class FoodProviderProfile(models.Model):
    """Profile model for users of type Food Provider."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='food_profile')
    
    # Business details
    business_name = models.CharField(_('Business Name'), max_length=200)
    business_registration_number = models.CharField(_('Business Registration Number'), max_length=50, blank=True, null=True)
    years_in_business = models.PositiveIntegerField(_('Years in Business'), default=0)
    
    # Food service details
    cuisine_types = models.TextField(_('Cuisine Types'), blank=True, null=True)
    special_diets_accommodated = models.TextField(_('Special Diets Accommodated'), blank=True, null=True)
    
    # Certifications
    food_safety_certification = models.CharField(_('Food Safety Certification'), max_length=100, blank=True, null=True)
    additional_certifications = models.TextField(_('Additional Certifications'), blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    
    class Meta:
        verbose_name = _('Food Provider Profile')
        verbose_name_plural = _('Food Provider Profiles')
    
    def __str__(self):
        return f"{self.business_name} - {self.user.get_full_name()}"