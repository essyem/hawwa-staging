from django.db import models
from django.conf import settings


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ChangeRequest(TimestampedModel):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('MERGED', 'Merged'),
        ('CLOSED', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='OPEN')
    priority = models.IntegerField(default=3)

    def __str__(self):
        return f"CR#{self.id} {self.title}"


class Incident(TimestampedModel):
    SEVERITY_CHOICES = [
        ('P1', 'Critical'),
        ('P2', 'High'),
        ('P3', 'Medium'),
        ('P4', 'Low'),
    ]

    title = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    severity = models.CharField(max_length=2, choices=SEVERITY_CHOICES, default='P3')
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"INC#{self.id} {self.title}"


class Lead(TimestampedModel):
    source = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name
