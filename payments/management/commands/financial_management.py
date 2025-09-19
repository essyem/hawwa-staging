from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Avg, Count
from decimal import Decimal
from datetime import timedelta

from payments.models import (
    Currency, Subscription, PaymentMethod, RecurringBilling, 
    PaymentReminder, FinancialForecast
)
from payments.services import SubscriptionService
from accounts.models import User
from services.models import Service

class Command(BaseCommand):
    help = 'Comprehensive financial management commands for Phase 2 Advanced Financial Features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup-currencies',
            action='store_true',
            help='Setup default currencies with exchange rates'
        )
        
        parser.add_argument(
            '--process-billing',
            action='store_true',
            help='Process all due recurring billing'
        )
        
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send due payment reminders'
        )
        
        parser.add_argument(
            '--create-sample-subscriptions',
            action='store_true',
            help='Create sample subscriptions for testing'
        )
        
        parser.add_argument(
            '--subscription-analytics',
            action='store_true',
            help='Display subscription analytics'
        )
        
        parser.add_argument(
            '--generate-forecasts',
            action='store_true',
            help='Generate financial forecasts'
        )
        
        parser.add_argument(
            '--update-exchange-rates',
            action='store_true',
            help='Update currency exchange rates'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Phase 2 Advanced Financial Features ===')
        )
        
        if options['setup_currencies']:
            self.setup_currencies()
        
        if options['process_billing']:
            self.process_billing()
        
        if options['send_reminders']:
            self.send_reminders()
        
        if options['create_sample_subscriptions']:
            self.create_sample_subscriptions()
        
        if options['subscription_analytics']:
            self.display_subscription_analytics()
        
        if options['generate_forecasts']:
            self.generate_forecasts()
        
        if options['update_exchange_rates']:
            self.update_exchange_rates()
        
        if not any(options.values()):
            self.display_help()

    def setup_currencies(self):
        """Setup default currencies with current exchange rates"""
        self.stdout.write("Setting up currencies...")
        
        currencies_data = [
            {'code': 'QAR', 'name': 'Qatari Riyal', 'symbol': '﷼', 'rate': Decimal('1.0000')},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'rate': Decimal('0.2747')},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'rate': Decimal('0.2531')},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'rate': Decimal('0.2179')},
            {'code': 'SAR', 'name': 'Saudi Riyal', 'symbol': 'ر.س', 'rate': Decimal('1.0302')},
            {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'د.إ', 'rate': Decimal('1.0091')},
            {'code': 'KWD', 'name': 'Kuwaiti Dinar', 'symbol': 'د.ك', 'rate': Decimal('0.0845')},
        ]
        
        created_count = 0
        updated_count = 0
        
        for currency_data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults={
                    'name': currency_data['name'],
                    'symbol': currency_data['symbol'],
                    'exchange_rate_to_qar': currency_data['rate'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Created {currency.code} - {currency.name}")
            else:
                # Update exchange rate
                currency.exchange_rate_to_qar = currency_data['rate']
                currency.save()
                updated_count += 1
                self.stdout.write(f"  ↻ Updated {currency.code} exchange rate")
        
        self.stdout.write(
            self.style.SUCCESS(f"Currency setup completed: {created_count} created, {updated_count} updated")
        )

    def process_billing(self):
        """Process all due recurring billing"""
        self.stdout.write("Processing recurring billing...")
        
        service = SubscriptionService()
        results = service.process_recurring_billing()
        
        self.stdout.write(f"  📈 Billing Results:")
        self.stdout.write(f"     Successfully processed: {results['processed']}")
        self.stdout.write(f"     Failed: {results['failed']}")
        
        # Display recent billing records
        recent_billing = RecurringBilling.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-created_at')[:5]
        
        if recent_billing:
            self.stdout.write(f"\n  📊 Recent Billing Records:")
            for billing in recent_billing:
                status_icon = "✅" if billing.status == 'completed' else "❌" if billing.status == 'failed' else "⏳"
                self.stdout.write(
                    f"     {status_icon} {billing.subscription.name} - "
                    f"{billing.currency.symbol}{billing.amount} ({billing.status})"
                )

    def send_reminders(self):
        """Send due payment reminders"""
        self.stdout.write("Processing payment reminders...")
        
        due_reminders = PaymentReminder.objects.filter(
            status='scheduled',
            scheduled_for__lte=timezone.now()
        ).select_related('user', 'subscription')
        
        sent_count = 0
        failed_count = 0
        
        for reminder in due_reminders:
            try:
                # Mock sending reminder (in real implementation, this would send actual emails/SMS)
                reminder.mark_sent()
                sent_count += 1
                
                self.stdout.write(
                    f"  📧 Sent {reminder.get_reminder_type_display()} to {reminder.user.get_full_name()}"
                )
                
            except Exception as e:
                reminder.mark_failed(str(e))
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Failed to send reminder to {reminder.user.get_full_name()}: {str(e)}")
                )
        
        self.stdout.write(f"\n  📈 Reminder Results: {sent_count} sent, {failed_count} failed")

    def create_sample_subscriptions(self):
        """Create sample subscriptions for testing"""
        self.stdout.write("Creating sample subscriptions...")
        
        # Get or create sample users and services
        users = User.objects.all()[:5]
        services = Service.objects.all()[:3]
        
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Please create users first."))
            return
        
        if not services:
            self.stdout.write(self.style.ERROR("No services found. Please create services first."))
            return
        
        # Get default currency
        qar_currency = Currency.objects.filter(code='QAR').first()
        if not qar_currency:
            self.stdout.write(self.style.ERROR("QAR currency not found. Please run --setup-currencies first."))
            return
        
        subscription_service = SubscriptionService()
        created_count = 0
        
        sample_plans = [
            {
                'name': 'Basic Home Cleaning',
                'base_price': '299.00',
                'billing_cycle': 'monthly',
                'trial_days': 7,
                'discount': '10.00'
            },
            {
                'name': 'Premium Wellness Package',
                'base_price': '599.00',
                'billing_cycle': 'monthly',
                'trial_days': 14,
                'discount': '15.00'
            },
            {
                'name': 'Annual Service Plan',
                'base_price': '2999.00',
                'billing_cycle': 'yearly',
                'trial_days': 30,
                'discount': '20.00'
            }
        ]
        
        for i, user in enumerate(users):
            if i < len(sample_plans):
                plan = sample_plans[i]
                service = services[i % len(services)]
                
                try:
                    subscription = subscription_service.create_subscription(
                        user=user,
                        service=service,
                        plan_data={
                            **plan,
                            'currency_id': qar_currency.id,
                            'auto_renew': True
                        }
                    )
                    created_count += 1
                    
                    self.stdout.write(
                        f"  ✓ Created subscription: {subscription.name} for {user.get_full_name()}"
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Failed to create subscription for {user.get_full_name()}: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"Sample subscription creation completed: {created_count} created")
        )

    def display_subscription_analytics(self):
        """Display comprehensive subscription analytics"""
        self.stdout.write("Generating subscription analytics...")
        
        service = SubscriptionService()
        analytics = service.get_subscription_analytics()
        
        self.stdout.write(f"\n  📊 Subscription Overview:")
        self.stdout.write(f"     Total Subscriptions: {analytics['total_subscriptions']}")
        self.stdout.write(f"     Active Subscriptions: {analytics['active_subscriptions']}")
        self.stdout.write(f"     Cancelled Subscriptions: {analytics['cancelled_subscriptions']}")
        
        self.stdout.write(f"\n  💰 Revenue Metrics:")
        revenue = analytics['revenue_metrics']
        self.stdout.write(f"     Total Revenue: QAR {revenue['total_revenue']:,.2f}")
        self.stdout.write(f"     Monthly Revenue: QAR {revenue['monthly_revenue']:,.2f}")
        self.stdout.write(f"     Average Subscription Value: QAR {revenue['average_subscription_value']:,.2f}")
        
        self.stdout.write(f"\n  📈 Growth & Churn:")
        churn = analytics['churn_analysis']
        growth = analytics['growth_metrics']
        self.stdout.write(f"     Monthly Churn Rate: {churn['monthly_churn_rate']}%")
        self.stdout.write(f"     Retention Rate: {churn['retention_rate']}%")
        self.stdout.write(f"     Monthly Growth Rate: {growth['monthly_growth_rate']}%")
        self.stdout.write(f"     New Subscriptions This Month: {growth['new_subscriptions_this_month']}")

    def generate_forecasts(self):
        """Generate financial forecasts"""
        self.stdout.write("Generating financial forecasts...")
        
        # Revenue forecast
        revenue_forecast = self._create_revenue_forecast()
        
        # Subscription growth forecast
        growth_forecast = self._create_growth_forecast()
        
        # Churn prediction
        churn_forecast = self._create_churn_forecast()
        
        self.stdout.write(f"\n  🔮 Generated Forecasts:")
        self.stdout.write(f"     Revenue Forecast: {revenue_forecast.title}")
        self.stdout.write(f"     Growth Forecast: {growth_forecast.title}")
        self.stdout.write(f"     Churn Prediction: {churn_forecast.title}")

    def _create_revenue_forecast(self):
        """Create revenue forecast"""
        # Calculate historical revenue for last 6 months
        historical_data = {}
        for i in range(6):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            monthly_revenue = RecurringBilling.objects.filter(
                status='completed',
                processed_at__gte=month_start,
                processed_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            historical_data[month_start.strftime('%Y-%m')] = float(monthly_revenue)
        
        # Simple linear projection for next 3 months
        current_revenue = list(historical_data.values())[0] if historical_data else 0
        predicted_revenue = current_revenue * 1.1  # 10% growth assumption
        
        forecast = FinancialForecast.objects.create(
            forecast_type='revenue',
            title='3-Month Revenue Forecast',
            description='Predicted revenue based on historical billing data',
            forecast_period_start=timezone.now().date(),
            forecast_period_end=(timezone.now() + timedelta(days=90)).date(),
            historical_data=historical_data,
            forecast_data={'predicted_monthly_revenue': predicted_revenue},
            confidence_score=Decimal('75.00'),
            accuracy_level='medium',
            predicted_revenue=Decimal(str(predicted_revenue)),
            predicted_growth_rate=Decimal('10.00'),
            algorithm_used='Linear Trend Analysis',
            data_points_used=len(historical_data)
        )
        
        return forecast

    def _create_growth_forecast(self):
        """Create subscription growth forecast"""
        current_active = Subscription.objects.filter(status__in=['active', 'trial']).count()
        predicted_growth = int(current_active * 1.15)  # 15% growth
        
        forecast = FinancialForecast.objects.create(
            forecast_type='subscription_growth',
            title='Subscription Growth Forecast',
            description='Predicted subscription growth based on current trends',
            forecast_period_start=timezone.now().date(),
            forecast_period_end=(timezone.now() + timedelta(days=90)).date(),
            historical_data={'current_active_subscriptions': current_active},
            forecast_data={'predicted_active_subscriptions': predicted_growth},
            confidence_score=Decimal('68.00'),
            accuracy_level='medium',
            predicted_growth_rate=Decimal('15.00'),
            algorithm_used='Growth Rate Analysis',
            data_points_used=current_active
        )
        
        return forecast

    def _create_churn_forecast(self):
        """Create churn prediction forecast"""
        total_subs = Subscription.objects.count()
        cancelled_last_month = Subscription.objects.filter(
            status='cancelled',
            updated_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        churn_rate = (cancelled_last_month / total_subs * 100) if total_subs > 0 else 0
        
        forecast = FinancialForecast.objects.create(
            forecast_type='churn_prediction',
            title='Customer Churn Prediction',
            description='Predicted customer churn based on cancellation patterns',
            forecast_period_start=timezone.now().date(),
            forecast_period_end=(timezone.now() + timedelta(days=30)).date(),
            historical_data={'cancelled_last_month': cancelled_last_month, 'total_subscriptions': total_subs},
            forecast_data={'predicted_churn_rate': churn_rate},
            confidence_score=Decimal('72.00'),
            accuracy_level='medium',
            risk_factors=['Payment failures', 'Service quality issues', 'Pricing sensitivity'],
            algorithm_used='Historical Churn Analysis',
            data_points_used=total_subs
        )
        
        return forecast

    def update_exchange_rates(self):
        """Update currency exchange rates (mock implementation)"""
        self.stdout.write("Updating exchange rates...")
        
        # In real implementation, this would fetch from currency API
        # Mock rate updates with small variations
        import random
        
        currencies = Currency.objects.exclude(code='QAR')
        updated_count = 0
        
        for currency in currencies:
            # Add small random variation to simulate rate changes
            variation = Decimal(str(random.uniform(-0.02, 0.02)))
            new_rate = currency.exchange_rate_to_qar + variation
            
            if new_rate > 0:
                currency.exchange_rate_to_qar = new_rate
                currency.save()
                updated_count += 1
                
                self.stdout.write(f"  ↻ {currency.code}: {new_rate:.4f} QAR")
        
        self.stdout.write(
            self.style.SUCCESS(f"Exchange rates updated: {updated_count} currencies")
        )

    def display_help(self):
        """Display available commands"""
        self.stdout.write("\n Available commands:")
        self.stdout.write("  --setup-currencies          Setup default currencies")
        self.stdout.write("  --process-billing           Process recurring billing")
        self.stdout.write("  --send-reminders            Send payment reminders")
        self.stdout.write("  --create-sample-subscriptions Create sample data")
        self.stdout.write("  --subscription-analytics    Display analytics")
        self.stdout.write("  --generate-forecasts        Generate forecasts")
        self.stdout.write("  --update-exchange-rates     Update currency rates")
        self.stdout.write("\n Example usage:")
        self.stdout.write("  python manage.py financial_management --setup-currencies")
        self.stdout.write("  python manage.py financial_management --subscription-analytics")