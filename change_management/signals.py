from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .models import ChangeRequest, Incident, Activity


def notify_subject(obj):
    return f"[Hawwa] Update: {obj}"


@receiver(post_save, sender=ChangeRequest)
def change_request_saved(sender, instance, created, **kwargs):
    verb = 'created' if created else 'updated'
    Activity.objects.create(actor=instance.reporter, verb=f'{verb} change request', target=str(instance))
    # send simple notification to assignee and reporter
    recipients = set()
    if instance.reporter and instance.reporter.email:
        recipients.add(instance.reporter.email)
    if instance.assignee and instance.assignee.email:
        recipients.add(instance.assignee.email)
    if recipients:
        send_mail(
            notify_subject(instance),
            instance.description or 'Change request updated.',
            settings.HAWWA_SETTINGS.get('SUPPORT_EMAIL'),
            list(recipients),
        )


@receiver(post_save, sender=Incident)
def incident_saved(sender, instance, created, **kwargs):
    verb = 'created' if created else 'updated'
    Activity.objects.create(actor=instance.reporter, verb=f'{verb} incident', target=str(instance))
    recipients = set()
    if instance.reporter and instance.reporter.email:
        recipients.add(instance.reporter.email)
    if recipients:
        send_mail(
            notify_subject(instance),
            instance.details or 'Incident updated.',
            settings.HAWWA_SETTINGS.get('SUPPORT_EMAIL'),
            list(recipients),
        )
