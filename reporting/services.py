from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import AnalyticsMetric, BusinessInsight, ReportTemplate, ReportGeneration
from accounts.models import User
from services.models import Service
from bookings.models import Booking
from financial.models import Invoice, Payment, Expense

class AnalyticsService:
    """Service class for generating business analytics and insights."""
    
    def __init__(self):
        self.today = timezone.now().date()
        self.current_month_start = self.today.replace(day=1)
        self.last_month_start = (self.current_month_start - timedelta(days=1)).replace(day=1)
        self.last_month_end = self.current_month_start - timedelta(days=1)
    
    def generate_financial_metrics(self, period_start=None, period_end=None):
        """Generate comprehensive financial metrics."""
        if not period_start:
            period_start = self.current_month_start
        if not period_end:
            period_end = self.today
        
        period_start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
        period_end_dt = timezone.make_aware(datetime.combine(period_end, datetime.max.time()))
        
        metrics = []
        
        # Total Revenue
        total_revenue = Invoice.objects.filter(
            status='paid',
            paid_date__range=[period_start_dt, period_end_dt]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        metrics.append(AnalyticsMetric(
            name='Total Revenue',
            metric_type='revenue',
            aggregation_type='sum',
            value=total_revenue,
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'currency': 'QAR', 'source': 'invoices'}
        ))
        
        # Outstanding Payments
        outstanding = Invoice.objects.filter(
            status__in=['sent', 'pending'],
            due_date__lte=self.today
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00')
        
        metrics.append(AnalyticsMetric(
            name='Outstanding Payments',
            metric_type='financial',
            aggregation_type='sum',
            value=outstanding,
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'currency': 'QAR', 'type': 'outstanding'}
        ))
        
        # Average Invoice Value
        avg_invoice = Invoice.objects.filter(
            created_at__range=[period_start_dt, period_end_dt]
        ).aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
        
        metrics.append(AnalyticsMetric(
            name='Average Invoice Value',
            metric_type='financial',
            aggregation_type='avg',
            value=avg_invoice,
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'currency': 'QAR', 'calculation': 'mean'}
        ))
        
        # Bulk create metrics
        AnalyticsMetric.objects.bulk_create(metrics)
        return metrics
    
    def generate_booking_metrics(self, period_start=None, period_end=None):
        """Generate booking-related metrics."""
        if not period_start:
            period_start = self.current_month_start
        if not period_end:
            period_end = self.today
        
        period_start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
        period_end_dt = timezone.make_aware(datetime.combine(period_end, datetime.max.time()))
        
        metrics = []
        
        # Total Bookings
        total_bookings = Booking.objects.filter(
            created_at__range=[period_start_dt, period_end_dt]
        ).count()
        
        metrics.append(AnalyticsMetric(
            name='Total Bookings',
            metric_type='booking',
            aggregation_type='count',
            value=Decimal(total_bookings),
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'unit': 'bookings'}
        ))
        
        # Booking Conversion Rate
        confirmed_bookings = Booking.objects.filter(
            created_at__range=[period_start_dt, period_end_dt],
            status='confirmed'
        ).count()
        
        conversion_rate = (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        metrics.append(AnalyticsMetric(
            name='Booking Conversion Rate',
            metric_type='booking',
            aggregation_type='percentage',
            value=Decimal(str(conversion_rate)),
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'unit': 'percentage', 'calculation': 'confirmed/total'}
        ))
        
        # Average Booking Value
        avg_booking_value = Booking.objects.filter(
            created_at__range=[period_start_dt, period_end_dt]
        ).aggregate(avg=Avg('total_price'))['avg'] or Decimal('0.00')
        
        metrics.append(AnalyticsMetric(
            name='Average Booking Value',
            metric_type='booking',
            aggregation_type='avg',
            value=avg_booking_value,
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'currency': 'QAR', 'source': 'booking_total_price'}
        ))
        
        AnalyticsMetric.objects.bulk_create(metrics)
        return metrics
    
    def generate_customer_metrics(self, period_start=None, period_end=None):
        """Generate customer-related metrics."""
        if not period_start:
            period_start = self.current_month_start
        if not period_end:
            period_end = self.today
        
        period_start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
        period_end_dt = timezone.make_aware(datetime.combine(period_end, datetime.max.time()))
        
        metrics = []
        
        # New Customers
        new_customers = User.objects.filter(
            date_joined__range=[period_start_dt, period_end_dt]
        ).count()
        
        metrics.append(AnalyticsMetric(
            name='New Customers',
            metric_type='customer',
            aggregation_type='count',
            value=Decimal(new_customers),
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'unit': 'customers', 'type': 'new_registrations'}
        ))
        
        # Active Customers (logged in within period)
        active_customers = User.objects.filter(
            last_login__range=[period_start_dt, period_end_dt]
        ).count()
        
        metrics.append(AnalyticsMetric(
            name='Active Customers',
            metric_type='customer',
            aggregation_type='count',
            value=Decimal(active_customers),
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'unit': 'customers', 'type': 'active_users'}
        ))
        
        # Customer Lifetime Value (CLV)
        customer_clv = Invoice.objects.filter(
            status='paid',
            paid_date__range=[period_start_dt, period_end_dt]
        ).values('customer').annotate(
            total_spent=Sum('total_amount')
        ).aggregate(avg_clv=Avg('total_spent'))['avg_clv'] or Decimal('0.00')
        
        metrics.append(AnalyticsMetric(
            name='Average Customer Lifetime Value',
            metric_type='customer',
            aggregation_type='avg',
            value=customer_clv,
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'currency': 'QAR', 'calculation': 'avg_total_spent'}
        ))
        
        AnalyticsMetric.objects.bulk_create(metrics)
        return metrics
    
    def generate_service_metrics(self, period_start=None, period_end=None):
        """Generate service performance metrics."""
        if not period_start:
            period_start = self.current_month_start
        if not period_end:
            period_end = self.today
        
        period_start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
        period_end_dt = timezone.make_aware(datetime.combine(period_end, datetime.max.time()))
        
        metrics = []
        
        # Service Utilization Rate
        total_services = Service.objects.filter(status='available').count()
        services_with_bookings = Service.objects.filter(
            bookings__created_at__range=[period_start_dt, period_end_dt]
        ).distinct().count()
        
        utilization_rate = (services_with_bookings / total_services * 100) if total_services > 0 else 0
        
        metrics.append(AnalyticsMetric(
            name='Service Utilization Rate',
            metric_type='service',
            aggregation_type='percentage',
            value=Decimal(str(utilization_rate)),
            period_start=period_start_dt,
            period_end=period_end_dt,
            metadata={'unit': 'percentage', 'calculation': 'services_booked/total_services'}
        ))
        
        # Top Performing Service
        top_service_data = Service.objects.filter(
            bookings__created_at__range=[period_start_dt, period_end_dt]
        ).annotate(
            booking_count=Count('bookings'),
            revenue=Sum('bookings__total_price')
        ).order_by('-revenue').first()
        
        if top_service_data:
            metrics.append(AnalyticsMetric(
                name='Top Service Revenue',
                metric_type='service',
                aggregation_type='max',
                value=top_service_data.revenue or Decimal('0.00'),
                period_start=period_start_dt,
                period_end=period_end_dt,
                metadata={
                    'service_name': top_service_data.name,
                    'service_id': top_service_data.id,
                    'booking_count': top_service_data.booking_count,
                    'currency': 'QAR'
                }
            ))
        
        AnalyticsMetric.objects.bulk_create(metrics)
        return metrics
    
    def generate_business_insights(self):
        """Generate AI-powered business insights based on current data."""
        insights = []
        
        # Revenue Trend Analysis
        current_revenue = Invoice.objects.filter(
            status='paid',
            paid_date__gte=self.current_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        last_month_revenue = Invoice.objects.filter(
            status='paid',
            paid_date__gte=self.last_month_start,
            paid_date__lte=self.last_month_end
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        if last_month_revenue > 0:
            growth_rate = ((current_revenue - last_month_revenue) / last_month_revenue) * 100
            
            if growth_rate > 20:
                insights.append(BusinessInsight(
                    title='Strong Revenue Growth Detected',
                    description=f'Revenue has increased by {growth_rate:.1f}% compared to last month. Current month revenue: QAR {current_revenue:.2f}',
                    insight_type='opportunity',
                    priority='high',
                    confidence_score=Decimal('85.0'),
                    recommended_actions='Consider scaling marketing efforts and expanding service offerings to capitalize on growth momentum.',
                    impact_estimate='High - Potential for sustained growth',
                    supporting_data={
                        'current_revenue': float(current_revenue),
                        'last_month_revenue': float(last_month_revenue),
                        'growth_rate': float(growth_rate)
                    }
                ))
            elif growth_rate < -10:
                insights.append(BusinessInsight(
                    title='Revenue Decline Alert',
                    description=f'Revenue has decreased by {abs(growth_rate):.1f}% compared to last month. Requires immediate attention.',
                    insight_type='risk',
                    priority='critical',
                    confidence_score=Decimal('90.0'),
                    recommended_actions='Analyze customer feedback, review pricing strategy, and implement retention campaigns.',
                    impact_estimate='High - Revenue recovery needed',
                    supporting_data={
                        'current_revenue': float(current_revenue),
                        'last_month_revenue': float(last_month_revenue),
                        'decline_rate': float(abs(growth_rate))
                    }
                ))
        
        # Booking Pattern Analysis
        pending_bookings = Booking.objects.filter(status='pending').count()
        total_bookings = Booking.objects.count()
        
        if total_bookings > 0:
            pending_rate = (pending_bookings / total_bookings) * 100
            
            if pending_rate > 30:
                insights.append(BusinessInsight(
                    title='High Pending Booking Rate',
                    description=f'{pending_rate:.1f}% of bookings are in pending status. This may indicate bottlenecks in the confirmation process.',
                    insight_type='operational',
                    priority='medium',
                    confidence_score=Decimal('75.0'),
                    recommended_actions='Review booking confirmation workflow and consider automated confirmation for certain service types.',
                    impact_estimate='Medium - Improved customer satisfaction',
                    supporting_data={
                        'pending_bookings': pending_bookings,
                        'total_bookings': total_bookings,
                        'pending_rate': float(pending_rate)
                    }
                ))
        
        # Customer Engagement Insights
        active_customers = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        total_customers = User.objects.count()
        
        if total_customers > 0:
            engagement_rate = (active_customers / total_customers) * 100
            
            if engagement_rate < 40:
                insights.append(BusinessInsight(
                    title='Low Customer Engagement',
                    description=f'Only {engagement_rate:.1f}% of customers have been active in the last 30 days.',
                    insight_type='opportunity',
                    priority='medium',
                    confidence_score=Decimal('80.0'),
                    recommended_actions='Implement email marketing campaigns, loyalty programs, and personalized service recommendations.',
                    impact_estimate='Medium - Increased customer retention',
                    supporting_data={
                        'active_customers': active_customers,
                        'total_customers': total_customers,
                        'engagement_rate': float(engagement_rate)
                    }
                ))
        
        # Outstanding Payments Alert
        overdue_amount = Invoice.objects.filter(
            due_date__lt=self.today,
            status__in=['sent', 'pending']
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00')
        
        if overdue_amount > 5000:  # QAR 5000 threshold
            overdue_count = Invoice.objects.filter(
                due_date__lt=self.today,
                status__in=['sent', 'pending']
            ).count()
            
            insights.append(BusinessInsight(
                title='Significant Overdue Payments',
                description=f'QAR {overdue_amount:.2f} in overdue payments across {overdue_count} invoices.',
                insight_type='risk',
                priority='high',
                confidence_score=Decimal('95.0'),
                recommended_actions='Send payment reminders, offer payment plans, and review credit policies.',
                impact_estimate='High - Cash flow improvement',
                supporting_data={
                    'overdue_amount': float(overdue_amount),
                    'overdue_count': overdue_count,
                    'threshold': 5000
                }
            ))
        
        # Bulk create insights
        BusinessInsight.objects.bulk_create(insights)
        return insights
    
    def generate_comprehensive_report(self, period_start=None, period_end=None):
        """Generate comprehensive analytics report."""
        financial_metrics = self.generate_financial_metrics(period_start, period_end)
        booking_metrics = self.generate_booking_metrics(period_start, period_end)
        customer_metrics = self.generate_customer_metrics(period_start, period_end)
        service_metrics = self.generate_service_metrics(period_start, period_end)
        insights = self.generate_business_insights()
        
        return {
            'financial_metrics': financial_metrics,
            'booking_metrics': booking_metrics,
            'customer_metrics': customer_metrics,
            'service_metrics': service_metrics,
            'business_insights': insights,
            'generation_time': timezone.now(),
            'period': {
                'start': period_start or self.current_month_start,
                'end': period_end or self.today
            }
        }
    
    def get_dashboard_data(self):
        """Get real-time dashboard data for visualization."""
        # Get latest metrics for dashboard
        latest_metrics = {}
        
        for metric_type in ['revenue', 'booking', 'customer', 'service', 'financial']:
            metrics = AnalyticsMetric.objects.filter(
                metric_type=metric_type
            ).order_by('-date_recorded')[:10]
            
            latest_metrics[metric_type] = [
                {
                    'name': m.name,
                    'value': float(m.value),
                    'date': m.date_recorded.isoformat(),
                    'aggregation': m.aggregation_type,
                    'metadata': m.metadata
                } for m in metrics
            ]
        
        # Get recent insights
        recent_insights = BusinessInsight.objects.filter(
            is_active=True,
            is_acknowledged=False
        ).order_by('-priority', '-created_at')[:5]
        
        insights_data = [
            {
                'title': i.title,
                'description': i.description,
                'type': i.insight_type,
                'priority': i.priority,
                'confidence': float(i.confidence_score),
                'actions': i.recommended_actions
            } for i in recent_insights
        ]
        
        return {
            'metrics': latest_metrics,
            'insights': insights_data,
            'last_updated': timezone.now().isoformat()
        }