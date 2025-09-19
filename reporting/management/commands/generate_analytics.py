from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import json

from reporting.services import AnalyticsService
from reporting.models import AnalyticsMetric, BusinessInsight, ReportTemplate

class Command(BaseCommand):
    help = 'Generate Phase 2 Enhanced Analytics and Business Intelligence'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--generate-metrics',
            action='store_true',
            help='Generate analytics metrics for current period',
        )
        parser.add_argument(
            '--generate-insights',
            action='store_true',
            help='Generate AI-powered business insights',
        )
        parser.add_argument(
            '--comprehensive-report',
            action='store_true',
            help='Generate comprehensive analytics report',
        )
        parser.add_argument(
            '--create-sample-templates',
            action='store_true',
            help='Create sample report templates',
        )
        parser.add_argument(
            '--dashboard-data',
            action='store_true',
            help='Show real-time dashboard data',
        )
        parser.add_argument(
            '--clear-old-data',
            action='store_true',
            help='Clear old analytics data (older than 6 months)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Phase 2 Enhanced Analytics System ==='))
        
        if options['generate_metrics']:
            self.generate_metrics()
        
        if options['generate_insights']:
            self.generate_insights()
            
        if options['comprehensive_report']:
            self.generate_comprehensive_report()
            
        if options['create_sample_templates']:
            self.create_sample_templates()
            
        if options['dashboard_data']:
            self.show_dashboard_data()
            
        if options['clear_old_data']:
            self.clear_old_data()
        
        if not any(options.values()):
            self.show_help()
    
    def generate_metrics(self):
        """Generate analytics metrics."""
        self.stdout.write(self.style.HTTP_INFO('Generating analytics metrics...'))
        
        analytics = AnalyticsService()
        
        try:
            # Generate metrics for current month
            financial_metrics = analytics.generate_financial_metrics()
            booking_metrics = analytics.generate_booking_metrics()
            customer_metrics = analytics.generate_customer_metrics()
            service_metrics = analytics.generate_service_metrics()
            
            total_metrics = (len(financial_metrics) + len(booking_metrics) + 
                           len(customer_metrics) + len(service_metrics))
            
            self.stdout.write(f'  ✓ Generated {len(financial_metrics)} financial metrics')
            self.stdout.write(f'  ✓ Generated {len(booking_metrics)} booking metrics')
            self.stdout.write(f'  ✓ Generated {len(customer_metrics)} customer metrics')
            self.stdout.write(f'  ✓ Generated {len(service_metrics)} service metrics')
            self.stdout.write(f'  📊 Total metrics generated: {total_metrics}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating metrics: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Metrics generation completed!'))
    
    def generate_insights(self):
        """Generate business insights."""
        self.stdout.write(self.style.HTTP_INFO('Generating business insights...'))
        
        analytics = AnalyticsService()
        
        try:
            insights = analytics.generate_business_insights()
            
            for insight in insights:
                priority_symbol = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠',
                    'critical': '🔴'
                }.get(insight.priority, '⚪')
                
                self.stdout.write(f'  {priority_symbol} {insight.title}')
                self.stdout.write(f'     Type: {insight.get_insight_type_display()}')
                self.stdout.write(f'     Confidence: {insight.confidence_score}%')
                
            self.stdout.write(f'  🧠 Total insights generated: {len(insights)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating insights: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Business insights generation completed!'))
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analytics report."""
        self.stdout.write(self.style.HTTP_INFO('Generating comprehensive analytics report...'))
        
        analytics = AnalyticsService()
        
        try:
            report = analytics.generate_comprehensive_report()
            
            self.stdout.write('  📈 Report Summary:')
            self.stdout.write(f'     Financial Metrics: {len(report["financial_metrics"])}')
            self.stdout.write(f'     Booking Metrics: {len(report["booking_metrics"])}')
            self.stdout.write(f'     Customer Metrics: {len(report["customer_metrics"])}')
            self.stdout.write(f'     Service Metrics: {len(report["service_metrics"])}')
            self.stdout.write(f'     Business Insights: {len(report["business_insights"])}')
            self.stdout.write(f'     Generated at: {report["generation_time"]}')
            
            # Show sample metrics
            self.stdout.write('\\n  📊 Sample Metrics:')
            for metric in report['financial_metrics'][:3]:
                self.stdout.write(f'     • {metric.name}: {metric.value}')
            
            # Show sample insights
            if report['business_insights']:
                self.stdout.write('\\n  🧠 Key Insights:')
                for insight in report['business_insights'][:2]:
                    self.stdout.write(f'     • {insight.title}')
                    self.stdout.write(f'       Priority: {insight.priority} | Confidence: {insight.confidence_score}%')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating report: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Comprehensive report generation completed!'))
    
    def create_sample_templates(self):
        """Create sample report templates."""
        self.stdout.write(self.style.HTTP_INFO('Creating sample report templates...'))
        
        templates = [
            {
                'name': 'Monthly Revenue Report',
                'description': 'Monthly revenue analysis with trends and projections',
                'report_type': 'financial',
                'chart_type': 'line',
                'data_source': 'financial.Invoice',
                'grouping': 'paid_date__month',
                'aggregation_field': 'total_amount',
                'aggregation_type': 'sum',
                'chart_title': 'Monthly Revenue Trend',
                'x_axis_label': 'Month',
                'y_axis_label': 'Revenue (QAR)',
                'is_automated': True,
                'schedule_frequency': 'monthly'
            },
            {
                'name': 'Customer Acquisition Dashboard',
                'description': 'Customer acquisition metrics and trends',
                'report_type': 'customer',
                'chart_type': 'bar',
                'data_source': 'accounts.User',
                'grouping': 'date_joined__month',
                'aggregation_field': 'id',
                'aggregation_type': 'count',
                'chart_title': 'New Customer Acquisitions',
                'x_axis_label': 'Month',
                'y_axis_label': 'New Customers',
                'is_automated': True,
                'schedule_frequency': 'weekly'
            },
            {
                'name': 'Service Performance Analysis',
                'description': 'Service booking performance and utilization rates',
                'report_type': 'service',
                'chart_type': 'pie',
                'data_source': 'services.Service',
                'grouping': 'category__name',
                'aggregation_field': 'bookings',
                'aggregation_type': 'count',
                'chart_title': 'Service Category Distribution',
                'x_axis_label': 'Service Category',
                'y_axis_label': 'Booking Count',
                'is_automated': False,
                'schedule_frequency': ''
            },
            {
                'name': 'Executive Summary Dashboard',
                'description': 'High-level KPIs for executive oversight',
                'report_type': 'executive',
                'chart_type': 'table',
                'data_source': 'reporting.AnalyticsMetric',
                'grouping': 'metric_type',
                'aggregation_field': 'value',
                'aggregation_type': 'avg',
                'chart_title': 'Executive KPI Summary',
                'x_axis_label': 'Metric Category',
                'y_axis_label': 'Average Value',
                'is_automated': True,
                'schedule_frequency': 'daily'
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f'  ✓ Created template: {template.name}')
                created_count += 1
            else:
                self.stdout.write(f'  ℹ Template already exists: {template.name}')
        
        self.stdout.write(f'  📋 Created {created_count} new report templates')
        self.stdout.write(self.style.SUCCESS('Sample templates creation completed!'))
    
    def show_dashboard_data(self):
        """Show real-time dashboard data."""
        self.stdout.write(self.style.HTTP_INFO('Fetching real-time dashboard data...'))
        
        analytics = AnalyticsService()
        
        try:
            dashboard_data = analytics.get_dashboard_data()
            
            self.stdout.write('  🎯 Dashboard Metrics Summary:')
            
            for metric_type, metrics in dashboard_data['metrics'].items():
                if metrics:
                    self.stdout.write(f'\\n  📊 {metric_type.title()} Metrics:')
                    for metric in metrics[:3]:  # Show top 3
                        value_display = f"QAR {metric['value']:.2f}" if 'currency' in metric.get('metadata', {}) else f"{metric['value']:.1f}"
                        self.stdout.write(f'     • {metric["name"]}: {value_display}')
            
            if dashboard_data['insights']:
                self.stdout.write('\\n  🧠 Active Insights:')
                for insight in dashboard_data['insights']:
                    priority_symbol = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'critical': '🔴'
                    }.get(insight['priority'], '⚪')
                    
                    self.stdout.write(f'     {priority_symbol} {insight["title"]}')
                    self.stdout.write(f'        Confidence: {insight["confidence"]:.0f}%')
            
            self.stdout.write(f'\\n  ⏰ Last updated: {dashboard_data["last_updated"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching dashboard data: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Dashboard data display completed!'))
    
    def clear_old_data(self):
        """Clear old analytics data."""
        self.stdout.write(self.style.HTTP_INFO('Clearing old analytics data...'))
        
        cutoff_date = timezone.now() - timedelta(days=180)  # 6 months
        
        try:
            # Clear old metrics
            old_metrics = AnalyticsMetric.objects.filter(date_recorded__lt=cutoff_date)
            metrics_count = old_metrics.count()
            old_metrics.delete()
            
            # Clear acknowledged insights older than 30 days
            old_insights = BusinessInsight.objects.filter(
                is_acknowledged=True,
                acknowledged_at__lt=timezone.now() - timedelta(days=30)
            )
            insights_count = old_insights.count()
            old_insights.delete()
            
            self.stdout.write(f'  🗑️ Deleted {metrics_count} old metrics')
            self.stdout.write(f'  🗑️ Deleted {insights_count} old insights')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error clearing old data: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Old data cleanup completed!'))
    
    def show_help(self):
        """Show available commands."""
        self.stdout.write('Available options:')
        self.stdout.write('  --generate-metrics         Generate analytics metrics')
        self.stdout.write('  --generate-insights        Generate business insights')
        self.stdout.write('  --comprehensive-report     Generate full analytics report')
        self.stdout.write('  --create-sample-templates  Create sample report templates')
        self.stdout.write('  --dashboard-data           Show real-time dashboard data')
        self.stdout.write('  --clear-old-data           Clear old analytics data')
        self.stdout.write('')
        self.stdout.write('Example usage:')
        self.stdout.write('  python manage.py generate_analytics --comprehensive-report')
        self.stdout.write('  python manage.py generate_analytics --generate-insights')
        self.stdout.write('  python manage.py generate_analytics --dashboard-data')