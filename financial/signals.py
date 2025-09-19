from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment, Expense
from .services.posting import create_payment_journal, create_expense_journal


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    # If payment just completed, create a journal entry
    if instance.payment_status == 'completed':
        try:
            create_payment_journal(instance)
        except Exception:
            # For now, swallow to avoid breaking flow
            pass


@receiver(post_save, sender=Expense)
def expense_post_save(sender, instance, created, **kwargs):
    # If expense marked as paid, create a journal entry
    if instance.is_paid and instance.payment_date:
        try:
            create_expense_journal(instance)
        except Exception:
            pass
