from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count
from datetime import timedelta
import logging

from payments.models import PaymentReminder, Subscription, RecurringBilling
from accounts.models import User

logger = logging.getLogger(__name__)

class ReminderService:
    """Automated payment reminder service with escalation logic"""
    
    def __init__(self):
        self.email_templates = {
            'upcoming_payment': {
                'subject': 'Upcoming Payment - {subscription_name}',
                'template': 'emails/reminders/upcoming_payment.html'
            },
            'overdue_payment': {
                'subject': 'URGENT: Overdue Payment - {subscription_name}',
                'template': 'emails/reminders/overdue_payment.html'
            },
            'failed_payment': {
                'subject': 'Payment Failed - Action Required',
                'template': 'emails/reminders/failed_payment.html'
            },
            'trial_ending': {
                'subject': 'Your trial ends soon - {subscription_name}',
                'template': 'emails/reminders/trial_ending.html'
            },
            'subscription_expiring': {
                'subject': 'Subscription Expiring - {subscription_name}',
                'template': 'emails/reminders/subscription_expiring.html'
            }
        }
    
    def create_upcoming_payment_reminders(self):
        """Create reminders for upcoming payments (3 days before)"""
        upcoming_date = timezone.now() + timedelta(days=3)
        
        subscriptions = Subscription.objects.filter(
            status__in=['active', 'trial'],
            next_billing_date__date=upcoming_date.date(),
            is_auto_renew=True
        ).exclude(
            payment_reminders__reminder_type='upcoming_payment',
            payment_reminders__status='scheduled',
            payment_reminders__scheduled_for__date=upcoming_date.date() - timedelta(days=3)
        )
        
        created_count = 0
        for subscription in subscriptions:
            reminder = self._create_reminder(
                user=subscription.user,
                subscription=subscription,
                reminder_type='upcoming_payment',
                escalation_level=1,
                scheduled_for=timezone.now() + timedelta(hours=1),
                subject=f"Upcoming Payment - {subscription.name}",
                message=self._generate_message('upcoming_payment', subscription)
            )
            if reminder:
                created_count += 1
        
        return created_count
    
    def create_overdue_payment_reminders(self):
        """Create reminders for overdue payments"""
        overdue_subscriptions = Subscription.objects.filter(
            status='past_due',
            next_billing_date__lt=timezone.now()
        )
        
        created_count = 0
        for subscription in overdue_subscriptions:
            days_overdue = (timezone.now() - subscription.next_billing_date).days
            
            # Escalate based on how overdue the payment is
            if days_overdue <= 3:
                escalation_level = 1
                scheduled_for = timezone.now() + timedelta(hours=2)
            elif days_overdue <= 7:
                escalation_level = 2
                scheduled_for = timezone.now() + timedelta(hours=1)
            elif days_overdue <= 14:
                escalation_level = 3
                scheduled_for = timezone.now() + timedelta(minutes=30)
            else:
                escalation_level = 4
                scheduled_for = timezone.now() + timedelta(minutes=15)
            
            # Check if we already have a recent reminder at this level
            recent_reminder = PaymentReminder.objects.filter(
                subscription=subscription,
                reminder_type='overdue_payment',
                escalation_level=escalation_level,
                created_at__gte=timezone.now() - timedelta(days=1)
            ).first()
            
            if not recent_reminder:
                reminder = self._create_reminder(
                    user=subscription.user,
                    subscription=subscription,
                    reminder_type='overdue_payment',
                    escalation_level=escalation_level,
                    scheduled_for=scheduled_for,
                    subject=f"URGENT: Payment Overdue - {subscription.name}",
                    message=self._generate_message('overdue_payment', subscription, days_overdue=days_overdue),
                    send_sms=(escalation_level >= 2)  # Send SMS for higher escalation levels
                )
                if reminder:
                    created_count += 1
        
        return created_count
    
    def create_failed_payment_reminders(self):
        """Create reminders for failed payments"""
        failed_billing = RecurringBilling.objects.filter(
            status='failed',
            created_at__gte=timezone.now() - timedelta(days=1)
        ).exclude(
            paymentreminder__reminder_type='failed_payment',
            paymentreminder__created_at__gte=timezone.now() - timedelta(hours=6)
        )
        
        created_count = 0
        for billing in failed_billing:
            reminder = self._create_reminder(
                user=billing.subscription.user,
                subscription=billing.subscription,
                billing_record=billing,
                reminder_type='failed_payment',
                escalation_level=billing.retry_count + 1,
                scheduled_for=timezone.now() + timedelta(minutes=30),
                subject=f"Payment Failed - {billing.subscription.name}",
                message=self._generate_message('failed_payment', billing.subscription, billing_record=billing),
                send_email=True,
                send_sms=(billing.retry_count >= 1)  # Send SMS after first retry
            )
            if reminder:
                created_count += 1
        
        return created_count
    
    def create_trial_ending_reminders(self):
        """Create reminders for trials ending soon"""
        trial_ending_date = timezone.now() + timedelta(days=2)
        
        trial_subscriptions = Subscription.objects.filter(
            status='trial',
            trial_end_date__date=trial_ending_date.date()
        ).exclude(
            payment_reminders__reminder_type='trial_ending',
            payment_reminders__status__in=['scheduled', 'sent'],
            payment_reminders__created_at__gte=timezone.now() - timedelta(days=1)
        )
        
        created_count = 0
        for subscription in trial_subscriptions:
            reminder = self._create_reminder(
                user=subscription.user,
                subscription=subscription,
                reminder_type='trial_ending',
                escalation_level=1,
                scheduled_for=timezone.now() + timedelta(hours=2),
                subject=f"Your trial ends soon - {subscription.name}",
                message=self._generate_message('trial_ending', subscription)
            )
            if reminder:
                created_count += 1
        
        return created_count
    
    def process_due_reminders(self):
        """Process and send all due reminders"""
        due_reminders = PaymentReminder.objects.filter(
            status='scheduled',
            scheduled_for__lte=timezone.now()
        ).select_related('user', 'subscription')
        
        sent_count = 0
        failed_count = 0
        
        for reminder in due_reminders:
            try:
                success = self._send_reminder(reminder)
                if success:
                    reminder.mark_sent()
                    sent_count += 1
                    
                    # Schedule escalation if needed
                    if reminder.escalation_level < 4 and reminder.reminder_type in ['overdue_payment', 'failed_payment']:
                        reminder.schedule_escalation(days_delay=3)
                        
                else:
                    reminder.mark_failed("Failed to send reminder")
                    failed_count += 1
                    
            except Exception as e:
                reminder.mark_failed(str(e))
                failed_count += 1
                logger.error(f"Failed to send reminder {reminder.id}: {str(e)}")
        
        return {'sent': sent_count, 'failed': failed_count}
    
    def _create_reminder(self, user, subscription, reminder_type, escalation_level, 
                        scheduled_for, subject, message, billing_record=None, 
                        send_email=True, send_sms=False, send_push=False):
        """Create a payment reminder"""
        try:
            reminder = PaymentReminder.objects.create(
                user=user,
                subscription=subscription,
                billing_record=billing_record,
                reminder_type=reminder_type,
                escalation_level=escalation_level,
                subject=subject,
                message=message,
                scheduled_for=scheduled_for,
                send_email=send_email,
                send_sms=send_sms,
                send_push=send_push
            )
            return reminder
        except Exception as e:
            logger.error(f"Failed to create reminder: {str(e)}")
            return None
    
    def _send_reminder(self, reminder):
        """Send reminder via configured channels"""
        success = True
        
        try:
            # Send email
            if reminder.send_email:
                email_success = self._send_email_reminder(reminder)
                success = success and email_success
            
            # Send SMS (mock implementation)
            if reminder.send_sms:
                sms_success = self._send_sms_reminder(reminder)
                success = success and sms_success
            
            # Send push notification (mock implementation)
            if reminder.send_push:
                push_success = self._send_push_reminder(reminder)
                success = success and push_success
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder.id}: {str(e)}")
            return False
    
    def _send_email_reminder(self, reminder):
        """Send email reminder"""
        try:
            template_info = self.email_templates.get(reminder.reminder_type)
            if not template_info:
                return False
            
            context = {
                'user': reminder.user,
                'subscription': reminder.subscription,
                'reminder': reminder,
                'billing_record': reminder.billing_record,
                'escalation_level': reminder.escalation_level
            }
            
            # For now, we'll send a simple text email since we don't have templates
            # In production, you would use the HTML templates
            
            send_mail(
                subject=reminder.subject,
                message=reminder.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reminder.user.email],
                fail_silently=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email reminder: {str(e)}")
            return False
    
    def _send_sms_reminder(self, reminder):
        """Send SMS reminder (mock implementation)"""
        try:
            # Mock SMS sending - in production, integrate with SMS gateway
            logger.info(f"SMS sent to {reminder.user.phone_number}: {reminder.subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS reminder: {str(e)}")
            return False
    
    def _send_push_reminder(self, reminder):
        """Send push notification (mock implementation)"""
        try:
            # Mock push notification - in production, integrate with push service
            logger.info(f"Push notification sent to {reminder.user.email}: {reminder.subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send push reminder: {str(e)}")
            return False
    
    def _generate_message(self, reminder_type, subscription, **kwargs):
        """Generate reminder message based on type"""
        messages = {
            'upcoming_payment': f"""
Dear {subscription.user.get_full_name()},

Your subscription for {subscription.name} will be automatically renewed in 3 days.

Amount: {subscription.currency.symbol}{subscription.get_effective_price()}
Next billing date: {subscription.next_billing_date.strftime('%B %d, %Y')}

If you need to update your payment method or cancel your subscription, please log into your account.

Thank you for choosing our services!
            """,
            
            'overdue_payment': f"""
URGENT: Payment Overdue

Dear {subscription.user.get_full_name()},

Your payment for {subscription.name} is now {kwargs.get('days_overdue', 0)} days overdue.

Amount due: {subscription.currency.symbol}{subscription.get_effective_price()}
Original due date: {subscription.next_billing_date.strftime('%B %d, %Y')}

Please update your payment method immediately to avoid service suspension.
            """,
            
            'failed_payment': f"""
Payment Failed - Action Required

Dear {subscription.user.get_full_name()},

We were unable to process your payment for {subscription.name}.

Amount: {subscription.currency.symbol}{subscription.get_effective_price()}
Reason: {kwargs.get('billing_record', {}).get('failure_reason', 'Payment declined')}

Please update your payment method to continue your subscription.
            """,
            
            'trial_ending': f"""
Your Trial Ends Soon

Dear {subscription.user.get_full_name()},

Your trial for {subscription.name} ends in 2 days.

Your subscription will automatically convert to a paid plan on {subscription.trial_end_date.strftime('%B %d, %Y')}.

Monthly cost: {subscription.currency.symbol}{subscription.get_effective_price()}

You can cancel anytime before the trial ends to avoid being charged.
            """,
            
            'subscription_expiring': f"""
Subscription Expiring

Dear {subscription.user.get_full_name()},

Your subscription for {subscription.name} is set to expire soon.

Expiration date: {subscription.end_date.strftime('%B %d, %Y') if subscription.end_date else 'N/A'}

Renew now to continue enjoying our services without interruption.
            """
        }
        
        return messages.get(reminder_type, "Payment reminder for your subscription.")


class Command(BaseCommand):
    help = 'Process automated payment reminders with escalation logic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-reminders',
            action='store_true',
            help='Create new payment reminders'
        )
        
        parser.add_argument(
            '--send-due-reminders',
            action='store_true',
            help='Send all due reminders'
        )
        
        parser.add_argument(
            '--reminder-stats',
            action='store_true',
            help='Display reminder statistics'
        )

    def handle(self, *args, **options):
        service = ReminderService()
        
        if options['create_reminders']:
            self.create_reminders(service)
        
        if options['send_due_reminders']:
            self.send_due_reminders(service)
        
        if options['reminder_stats']:
            self.display_reminder_stats()
        
        if not any(options.values()):
            self.stdout.write("Use --help to see available options")

    def create_reminders(self, service):
        self.stdout.write("Creating payment reminders...")
        
        upcoming = service.create_upcoming_payment_reminders()
        overdue = service.create_overdue_payment_reminders()
        failed = service.create_failed_payment_reminders()
        trial = service.create_trial_ending_reminders()
        
        self.stdout.write(f"  📧 Created reminders:")
        self.stdout.write(f"     Upcoming payments: {upcoming}")
        self.stdout.write(f"     Overdue payments: {overdue}")
        self.stdout.write(f"     Failed payments: {failed}")
        self.stdout.write(f"     Trial endings: {trial}")

    def send_due_reminders(self, service):
        self.stdout.write("Sending due reminders...")
        
        results = service.process_due_reminders()
        
        self.stdout.write(f"  📤 Reminder results:")
        self.stdout.write(f"     Sent successfully: {results['sent']}")
        self.stdout.write(f"     Failed to send: {results['failed']}")

    def display_reminder_stats(self):
        self.stdout.write("Payment reminder statistics...")
        
        total_reminders = PaymentReminder.objects.count()
        scheduled = PaymentReminder.objects.filter(status='scheduled').count()
        sent = PaymentReminder.objects.filter(status='sent').count()
        failed = PaymentReminder.objects.filter(status='failed').count()
        
        self.stdout.write(f"  📊 Reminder Overview:")
        self.stdout.write(f"     Total reminders: {total_reminders}")
        self.stdout.write(f"     Scheduled: {scheduled}")
        self.stdout.write(f"     Sent: {sent}")
        self.stdout.write(f"     Failed: {failed}")
        
        # Recent reminders by type
        recent_reminders = PaymentReminder.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).values('reminder_type').annotate(count=Count('id'))
        
        if recent_reminders:
            self.stdout.write(f"\n  📅 Recent reminders (last 7 days):")
            for reminder_info in recent_reminders:
                self.stdout.write(f"     {reminder_info['reminder_type']}: {reminder_info['count']}")