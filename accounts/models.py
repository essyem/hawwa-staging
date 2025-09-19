from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Custom manager for the User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for all users of the system."""
    
    USER_TYPE_CHOICES = (
        ('MOTHER', _('Mother')),
        ('ACCOMMODATION', _('Accommodation Provider')),
        ('CARETAKER', _('Caretaker Provider')),
        ('WELLNESS', _('Wellness Service Provider')),
        ('MEDITATION', _('Meditation Consultant')),
        ('MENTAL_HEALTH', _('Mental Health Consultant')),
        ('FOOD', _('Food Provider')),
        ('ADMIN', _('Administrator')),
    )
    
    email = models.EmailField(_('Email Address'), unique=True)
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    phone = models.CharField(_('Phone Number'), max_length=20, blank=True)
    user_type = models.CharField(_('User Type'), max_length=20, choices=USER_TYPE_CHOICES)
    
    # Profile picture
    profile_picture = models.ImageField(_('Profile Picture'), upload_to='profile_pics/', blank=True, null=True)
    
    # Common fields
    date_joined = models.DateTimeField(_('Date Joined'), default=timezone.now)
    is_active = models.BooleanField(_('Active'), default=True)
    is_staff = models.BooleanField(_('Staff Status'), default=False)
    is_verified = models.BooleanField(_('Email Verified'), default=False)
    
    # Location fields
    address = models.CharField(_('Address'), max_length=255, blank=True, null=True)
    city = models.CharField(_('City'), max_length=100, blank=True, null=True)
    state = models.CharField(_('State/Province'), max_length=100, blank=True, null=True)
    country = models.CharField(_('Country'), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True, null=True)
    
    # Notification preferences
    receive_emails = models.BooleanField(_('Receive Email Notifications'), default=True)
    receive_sms = models.BooleanField(_('Receive SMS Notifications'), default=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
