from django.utils import timezone
from django.db.models import Q, Sum, Avg, Count
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from datetime import timedelta, date
import logging

from .models import (
    Subscription, RecurringBilling, PaymentReminder, 
    FinancialForecast, Currency, PaymentMethod, ExchangeRateHistory
)
from accounts.models import User

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Comprehensive subscription management service"""
    
    def create_subscription(self, user, service, plan_data):
        """Create a new subscription with trial period"""
        try:
            # Create subscription
            subscription = Subscription.objects.create(
                user=user,
                service=service,
                name=plan_data.get('name', f"{service.name} Subscription"),
                description=plan_data.get('description', ''),
                billing_cycle=plan_data.get('billing_cycle', 'monthly'),
                base_price=Decimal(str(plan_data.get('base_price', '0.00'))),
                currency_id=plan_data.get('currency_id', 1),  # Default to QAR
                discount_percentage=Decimal(str(plan_data.get('discount', '0.00'))),
                trial_end_date=timezone.now() + timedelta(days=plan_data.get('trial_days', 7)),
                next_billing_date=timezone.now() + timedelta(days=plan_data.get('trial_days', 7)),
                payment_method=plan_data.get('payment_method'),
                status='trial',
                is_auto_renew=plan_data.get('auto_renew', True)
            )
            
            # Schedule trial ending reminder
            self._schedule_trial_ending_reminder(subscription)
            
            logger.info(f"Created subscription {subscription.id} for user {user.id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise

    def upgrade_subscription(self, subscription, new_plan_data):
        """Upgrade or downgrade subscription plan"""
        try:
            # Calculate prorated amount for immediate billing
            old_price = subscription.get_effective_price()
            new_price = Decimal(str(new_plan_data.get('base_price', old_price)))
            
            # Update subscription details
            subscription.base_price = new_price
            subscription.billing_cycle = new_plan_data.get('billing_cycle', subscription.billing_cycle)
            subscription.discount_percentage = Decimal(str(new_plan_data.get('discount', subscription.discount_percentage)))
            
            # Handle immediate billing for upgrades
            if new_price > old_price:
                prorated_amount = self._calculate_prorated_amount(subscription, old_price, new_price)
                if prorated_amount > 0:
                    self._create_prorated_billing(subscription, prorated_amount)
            
            # Update next billing date based on new cycle
            subscription.next_billing_date = subscription.calculate_next_billing_date()
            subscription.save()
            
            # Log the change
            subscription.metadata['upgrade_history'] = subscription.metadata.get('upgrade_history', [])
            subscription.metadata['upgrade_history'].append({
                'date': timezone.now().isoformat(),
                'old_price': float(old_price),
                'new_price': float(new_price),
                'old_cycle': subscription.billing_cycle,
                'new_cycle': new_plan_data.get('billing_cycle', subscription.billing_cycle)
            })
            subscription.save()
            
            logger.info(f"Upgraded subscription {subscription.id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to upgrade subscription {subscription.id}: {str(e)}")
            raise

    def cancel_subscription(self, subscription, reason="", immediate=False):
        """Cancel subscription with optional immediate termination"""
        try:
            if immediate:
                subscription.status = 'cancelled'
                subscription.end_date = timezone.now()
            else:
                # Cancel at end of billing period
                subscription.status = 'cancelled'
                subscription.is_auto_renew = False
                subscription.end_date = subscription.next_billing_date
            
            # Add cancellation metadata
            subscription.metadata['cancellation'] = {
                'date': timezone.now().isoformat(),
                'reason': reason,
                'immediate': immediate,
                'cancelled_by': 'user'  # Could be 'admin', 'system', etc.
            }
            subscription.save()
            
            # Cancel pending payment reminders
            PaymentReminder.objects.filter(
                subscription=subscription,
                status='scheduled'
            ).update(status='cancelled')
            
            # Send cancellation confirmation email
            self._send_cancellation_email(subscription, reason)
            
            logger.info(f"Cancelled subscription {subscription.id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription.id}: {str(e)}")
            raise

    def process_recurring_billing(self):
        """Process all due recurring billing"""
        due_subscriptions = Subscription.objects.filter(
            status__in=['active', 'trial'],
            next_billing_date__lte=timezone.now(),
            is_auto_renew=True
        )
        
        processed_count = 0
        failed_count = 0
        
        for subscription in due_subscriptions:
            try:
                billing_record = self._create_billing_record(subscription)
                
                if self._process_payment(billing_record):
                    billing_record.mark_completed()
                    processed_count += 1
                    
                    # Update subscription status from trial to active
                    if subscription.status == 'trial':
                        subscription.status = 'active'
                        subscription.save()
                        
                else:
                    billing_record.mark_failed("Payment processing failed")
                    self._handle_failed_payment(subscription, billing_record)
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process billing for subscription {subscription.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Processed recurring billing: {processed_count} successful, {failed_count} failed")
        return {'processed': processed_count, 'failed': failed_count}

    def get_subscription_analytics(self, user=None):
        """Get comprehensive subscription analytics"""
        queryset = Subscription.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        analytics = {
            'total_subscriptions': queryset.count(),
            'active_subscriptions': queryset.filter(status__in=['active', 'trial']).count(),
            'cancelled_subscriptions': queryset.filter(status='cancelled').count(),
            'revenue_metrics': self._calculate_revenue_metrics(queryset),
            'churn_analysis': self._analyze_churn(queryset),
            'growth_metrics': self._calculate_growth_metrics(queryset),
        }
        
        return analytics

    def _calculate_prorated_amount(self, subscription, old_price, new_price):
        """Calculate prorated amount for plan changes"""
        days_in_cycle = self._get_days_in_billing_cycle(subscription.billing_cycle)
        days_remaining = subscription.days_until_next_billing()
        
        if days_remaining and days_in_cycle:
            price_difference = new_price - old_price
            return (price_difference * days_remaining) / days_in_cycle
        
        return Decimal('0.00')

    def _get_days_in_billing_cycle(self, billing_cycle):
        """Get number of days in billing cycle"""
        cycle_days = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        return cycle_days.get(billing_cycle, 30)

    def _create_billing_record(self, subscription):
        """Create billing record for subscription"""
        period_start = subscription.last_billing_date or subscription.start_date
        period_end = subscription.next_billing_date
        
        return RecurringBilling.objects.create(
            subscription=subscription,
            amount=subscription.get_effective_price(),
            currency=subscription.currency,
            billing_period_start=period_start,
            billing_period_end=period_end,
            payment_method=subscription.payment_method,
            status='pending'
        )

    def _create_prorated_billing(self, subscription, amount):
        """Create immediate prorated billing"""
        return RecurringBilling.objects.create(
            subscription=subscription,
            amount=amount,
            currency=subscription.currency,
            billing_period_start=timezone.now(),
            billing_period_end=timezone.now(),
            payment_method=subscription.payment_method,
            status='pending'
        )

    def _process_payment(self, billing_record):
        """Process payment for billing record (mock implementation)"""
        # This would integrate with actual payment gateways
        # For now, we'll simulate payment processing
        
        try:
            # Simulate payment gateway call
            # In real implementation, this would call Stripe, PayPal, etc.
            
            # Mock success/failure (90% success rate for simulation)
            import random
            success = random.random() > 0.1
            
            if success:
                billing_record.gateway_transaction_id = f"tx_{timezone.now().strftime('%Y%m%d%H%M%S')}"
                billing_record.gateway_response = {
                    'status': 'success',
                    'transaction_id': billing_record.gateway_transaction_id,
                    'amount': float(billing_record.amount),
                    'currency': billing_record.currency.code,
                    'processed_at': timezone.now().isoformat()
                }
                return True
            else:
                billing_record.gateway_response = {
                    'status': 'failed',
                    'error': 'Insufficient funds',
                    'error_code': 'INSUFFICIENT_FUNDS'
                }
                return False
                
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return False

    def _handle_failed_payment(self, subscription, billing_record):
        """Handle failed payment scenarios"""
        try:
            # Update subscription status
            subscription.status = 'past_due'
            subscription.save()
            
            # Schedule payment retry
            billing_record.schedule_retry()
            
            # Create payment reminder
            PaymentReminder.objects.create(
                user=subscription.user,
                subscription=subscription,
                billing_record=billing_record,
                reminder_type='failed_payment',
                escalation_level=1,
                subject=f"Payment Failed - {subscription.name}",
                message=f"Your payment for {subscription.name} has failed. Please update your payment method.",
                scheduled_for=timezone.now() + timedelta(hours=1),
                send_email=True,
                send_sms=False
            )
            
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {str(e)}")

    def _schedule_trial_ending_reminder(self, subscription):
        """Schedule reminder for trial ending"""
        if subscription.trial_end_date:
            reminder_date = subscription.trial_end_date - timedelta(days=2)
            
            PaymentReminder.objects.create(
                user=subscription.user,
                subscription=subscription,
                reminder_type='trial_ending',
                escalation_level=1,
                subject=f"Your {subscription.name} trial ends soon",
                message=f"Your trial for {subscription.name} ends in 2 days. Your subscription will auto-renew unless cancelled.",
                scheduled_for=reminder_date,
                send_email=True
            )

    def _send_cancellation_email(self, subscription, reason):
        """Send cancellation confirmation email"""
        try:
            context = {
                'subscription': subscription,
                'user': subscription.user,
                'reason': reason,
                'end_date': subscription.end_date
            }
            
            subject = f"Subscription Cancelled - {subscription.name}"
            message = render_to_string('emails/subscription_cancelled.txt', context)
            html_message = render_to_string('emails/subscription_cancelled.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {str(e)}")

    def _calculate_revenue_metrics(self, queryset):
        """Calculate revenue metrics for subscriptions"""
        billing_records = RecurringBilling.objects.filter(
            subscription__in=queryset,
            status='completed'
        )
        
        total_revenue = billing_records.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        monthly_revenue = billing_records.filter(
            processed_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return {
            'total_revenue': float(total_revenue),
            'monthly_revenue': float(monthly_revenue),
            'average_subscription_value': float(
                queryset.filter(status='active').aggregate(
                    avg=Avg('base_price')
                )['avg'] or Decimal('0.00')
            )
        }

    def _analyze_churn(self, queryset):
        """Analyze subscription churn"""
        total_subscriptions = queryset.count()
        cancelled_this_month = queryset.filter(
            status='cancelled',
            updated_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        churn_rate = (cancelled_this_month / total_subscriptions * 100) if total_subscriptions > 0 else 0
        
        return {
            'monthly_churn_rate': round(churn_rate, 2),
            'cancelled_this_month': cancelled_this_month,
            'retention_rate': round(100 - churn_rate, 2)
        }

    def _calculate_growth_metrics(self, queryset):
        """Calculate subscription growth metrics"""
        current_month = timezone.now().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_month_subscriptions = queryset.filter(
            created_at__gte=current_month
        ).count()
        
        last_month_subscriptions = queryset.filter(
            created_at__gte=last_month,
            created_at__lt=current_month
        ).count()
        
        growth_rate = 0
        if last_month_subscriptions > 0:
            growth_rate = ((current_month_subscriptions - last_month_subscriptions) / last_month_subscriptions) * 100
        
        return {
            'monthly_growth_rate': round(growth_rate, 2),
            'new_subscriptions_this_month': current_month_subscriptions,
            'new_subscriptions_last_month': last_month_subscriptions
        }