"""
Management command to generate comprehensive analytics reports
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q, Max, Min
from datetime import datetime, timedelta, date
from decimal import Decimal
import csv
import json
import logging

from analytics.models import QualityScore, PerformanceMetrics, VendorRanking, QualityCertification
from vendors.models import VendorProfile
from bookings.models import Booking
from services.models import ServiceReview, ServiceCategory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate comprehensive analytics reports for vendors and platform performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['quality', 'performance', 'rankings', 'summary', 'all'],
            default='summary',
            help='Type of report to generate',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Generate report for specific vendor ID',
        )
        parser.add_argument(
            '--category-id',
            type=int,
            help='Generate report for specific service category ID',
        )
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['console', 'csv', 'json'],
            default='console',
            help='Output format for the report',
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path (required for csv/json formats)',
        )
        parser.add_argument(
            '--top-n',
            type=int,
            default=10,
            help='Number of top performers to include (default: 10)',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Validate output file requirement
        if options['output_format'] in ['csv', 'json'] and not options['output_file']:
            raise CommandError("Output file path is required for csv/json formats")
        
        # Determine date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=options['days'])
        
        self.stdout.write(f"Generating {options['report_type']} report for period: {start_date} to {end_date}")
        
        # Generate report based on type
        if options['report_type'] == 'quality':
            report_data = self._generate_quality_report(start_date, end_date, options)
        elif options['report_type'] == 'performance':
            report_data = self._generate_performance_report(start_date, end_date, options)
        elif options['report_type'] == 'rankings':
            report_data = self._generate_rankings_report(start_date, end_date, options)
        elif options['report_type'] == 'summary':
            report_data = self._generate_summary_report(start_date, end_date, options)
        elif options['report_type'] == 'all':
            report_data = self._generate_comprehensive_report(start_date, end_date, options)
        
        # Output report
        if options['output_format'] == 'console':
            self._output_console(report_data, options)
        elif options['output_format'] == 'csv':
            self._output_csv(report_data, options)
        elif options['output_format'] == 'json':
            self._output_json(report_data, options)
        
        self.stdout.write(
            self.style.SUCCESS(f"Report generated successfully!")
        )
    
    def _generate_quality_report(self, start_date, end_date, options):
        """Generate quality scores report"""
        
        # Base queryset
        quality_scores = QualityScore.objects.filter(
            period_start__gte=start_date,
            period_end__lte=end_date
        ).select_related('vendor', 'vendor__user')
        
        # Filter by vendor if specified
        if options['vendor_id']:
            quality_scores = quality_scores.filter(vendor_id=options['vendor_id'])
        
        # Get latest scores for each vendor
        latest_scores = {}
        for score in quality_scores.order_by('-calculated_at'):
            if score.vendor.id not in latest_scores:
                latest_scores[score.vendor.id] = score
        
        # Sort by overall score
        sorted_scores = sorted(latest_scores.values(), key=lambda x: x.overall_score, reverse=True)
        
        # Limit to top N
        top_scores = sorted_scores[:options['top_n']]
        
        return {
            'report_type': 'Quality Scores Report',
            'period': f"{start_date} to {end_date}",
            'total_vendors': len(sorted_scores),
            'data': [
                {
                    'rank': idx + 1,
                    'vendor_name': score.vendor.business_name,
                    'vendor_id': score.vendor.id,
                    'overall_score': float(score.overall_score),
                    'grade': score.grade,
                    'customer_ratings_score': float(score.customer_ratings_score),
                    'completion_rate_score': float(score.completion_rate_score),
                    'response_time_score': float(score.response_time_score),
                    'repeat_customers_score': float(score.repeat_customers_score),
                    'performance_trends_score': float(score.performance_trends_score),
                    'total_bookings': score.total_bookings,
                    'avg_rating': float(score.avg_rating),
                    'calculated_at': score.calculated_at.isoformat(),
                }
                for idx, score in enumerate(top_scores)
            ]
        }
    
    def _generate_performance_report(self, start_date, end_date, options):
        """Generate performance metrics report"""
        
        # Aggregate performance metrics
        metrics = PerformanceMetrics.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('vendor', 'vendor__user')
        
        # Filter by vendor if specified
        if options['vendor_id']:
            metrics = metrics.filter(vendor_id=options['vendor_id'])
        
        # Aggregate by vendor
        vendor_metrics = {}
        for metric in metrics:
            vendor_id = metric.vendor.id
            if vendor_id not in vendor_metrics:
                vendor_metrics[vendor_id] = {
                    'vendor': metric.vendor,
                    'total_bookings_received': 0,
                    'total_bookings_completed': 0,
                    'total_revenue': Decimal('0.00'),
                    'total_ratings': 0,
                    'rating_sum': 0,
                    'total_customers': 0,
                    'total_repeat_customers': 0,
                }
            
            vm = vendor_metrics[vendor_id]
            vm['total_bookings_received'] += metric.bookings_received
            vm['total_bookings_completed'] += metric.bookings_completed
            vm['total_revenue'] += metric.revenue
            vm['total_ratings'] += metric.total_ratings
            vm['rating_sum'] += metric.avg_rating * metric.total_ratings
            vm['total_customers'] += metric.total_unique_customers
            vm['total_repeat_customers'] += metric.repeat_customers
        
        # Calculate derived metrics and sort
        performance_data = []
        for vendor_id, vm in vendor_metrics.items():
            completion_rate = (vm['total_bookings_completed'] / vm['total_bookings_received'] * 100) if vm['total_bookings_received'] > 0 else 0
            avg_rating = (vm['rating_sum'] / vm['total_ratings']) if vm['total_ratings'] > 0 else 0
            repeat_rate = (vm['total_repeat_customers'] / vm['total_customers'] * 100) if vm['total_customers'] > 0 else 0
            
            performance_data.append({
                'vendor_name': vm['vendor'].business_name,
                'vendor_id': vendor_id,
                'total_bookings': vm['total_bookings_received'],
                'completion_rate': round(completion_rate, 2),
                'total_revenue': float(vm['total_revenue']),
                'avg_rating': round(avg_rating, 2),
                'total_ratings': vm['total_ratings'],
                'repeat_customer_rate': round(repeat_rate, 2),
                'total_customers': vm['total_customers'],
            })
        
        # Sort by revenue
        performance_data.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return {
            'report_type': 'Performance Metrics Report',
            'period': f"{start_date} to {end_date}",
            'total_vendors': len(performance_data),
            'data': performance_data[:options['top_n']]
        }
    
    def _generate_rankings_report(self, start_date, end_date, options):
        """Generate vendor rankings report"""
        
        rankings = VendorRanking.objects.filter(
            period_start__gte=start_date,
            period_end__lte=end_date
        ).select_related('vendor', 'service_category').order_by('overall_rank')
        
        # Filter by vendor if specified
        if options['vendor_id']:
            rankings = rankings.filter(vendor_id=options['vendor_id'])
        
        # Filter by category if specified
        if options['category_id']:
            rankings = rankings.filter(service_category_id=options['category_id'])
        
        return {
            'report_type': 'Vendor Rankings Report',
            'period': f"{start_date} to {end_date}",
            'total_rankings': rankings.count(),
            'data': [
                {
                    'overall_rank': ranking.overall_rank,
                    'vendor_name': ranking.vendor.business_name,
                    'vendor_id': ranking.vendor.id,
                    'category': ranking.service_category.name if ranking.service_category else 'Overall',
                    'quality_score': float(ranking.quality_score),
                    'performance_score': float(ranking.performance_score),
                    'customer_satisfaction_score': float(ranking.customer_satisfaction_score),
                    'percentile': round(ranking.percentile, 1),
                    'total_vendors': ranking.total_vendors,
                }
                for ranking in rankings[:options['top_n']]
            ]
        }
    
    def _generate_summary_report(self, start_date, end_date, options):
        """Generate platform summary report"""
        
        # Platform-wide statistics
        total_vendors = VendorProfile.objects.filter(status='active').count()
        total_bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).count()
        
        completed_bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='completed'
        ).count()
        
        total_revenue = Booking.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        
        avg_rating = ServiceReview.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Quality score statistics
        quality_scores = QualityScore.objects.filter(
            period_start__gte=start_date,
            period_end__lte=end_date
        )
        
        avg_quality_score = quality_scores.aggregate(avg=Avg('overall_score'))['avg'] or 0
        
        # Top performers
        top_vendors = quality_scores.order_by('-overall_score')[:5]
        
        return {
            'report_type': 'Platform Summary Report',
            'period': f"{start_date} to {end_date}",
            'platform_stats': {
                'total_active_vendors': total_vendors,
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings,
                'completion_rate': round((completed_bookings / total_bookings * 100) if total_bookings > 0 else 0, 2),
                'total_revenue': float(total_revenue),
                'avg_platform_rating': round(float(avg_rating), 2),
                'avg_quality_score': round(float(avg_quality_score), 2),
            },
            'top_performers': [
                {
                    'vendor_name': score.vendor.business_name,
                    'quality_score': float(score.overall_score),
                    'grade': score.grade,
                }
                for score in top_vendors
            ]
        }
    
    def _generate_comprehensive_report(self, start_date, end_date, options):
        """Generate comprehensive report with all metrics"""
        
        return {
            'quality_report': self._generate_quality_report(start_date, end_date, options),
            'performance_report': self._generate_performance_report(start_date, end_date, options),
            'rankings_report': self._generate_rankings_report(start_date, end_date, options),
            'summary_report': self._generate_summary_report(start_date, end_date, options),
        }
    
    def _output_console(self, data, options):
        """Output report to console"""
        
        if 'quality_report' in data:  # Comprehensive report
            for report_name, report_data in data.items():
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"{report_data['report_type']}")
                self.stdout.write(f"{'='*60}")
                self._print_report_data(report_data)
        else:  # Single report
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"{data['report_type']}")
            self.stdout.write(f"{'='*60}")
            self._print_report_data(data)
    
    def _print_report_data(self, data):
        """Print report data to console"""
        
        if 'platform_stats' in data:  # Summary report
            stats = data['platform_stats']
            self.stdout.write(f"Platform Statistics:")
            self.stdout.write(f"  Active Vendors: {stats['total_active_vendors']}")
            self.stdout.write(f"  Total Bookings: {stats['total_bookings']}")
            self.stdout.write(f"  Completion Rate: {stats['completion_rate']}%")
            self.stdout.write(f"  Total Revenue: ${stats['total_revenue']:,.2f}")
            self.stdout.write(f"  Average Rating: {stats['avg_platform_rating']:.1f}★")
            self.stdout.write(f"  Average Quality Score: {stats['avg_quality_score']:.1f}/100")
            
            self.stdout.write(f"\nTop Performers:")
            for performer in data['top_performers']:
                self.stdout.write(f"  {performer['vendor_name']}: {performer['quality_score']:.1f}/100 ({performer['grade']})")
        
        elif 'data' in data:  # Regular report with data array
            for item in data['data'][:10]:  # Show top 10
                if 'overall_score' in item:  # Quality report
                    self.stdout.write(f"#{item['rank']} {item['vendor_name']}: {item['overall_score']:.1f}/100 ({item['grade']})")
                elif 'total_revenue' in item:  # Performance report
                    self.stdout.write(f"{item['vendor_name']}: ${item['total_revenue']:,.2f} revenue, {item['completion_rate']:.1f}% completion")
                elif 'overall_rank' in item:  # Rankings report
                    self.stdout.write(f"#{item['overall_rank']} {item['vendor_name']} ({item['category']}): {item['quality_score']:.1f} quality")
    
    def _output_csv(self, data, options):
        """Output report to CSV file"""
        
        with open(options['output_file'], 'w', newline='', encoding='utf-8') as csvfile:
            if 'data' in data and data['data']:
                # Get field names from first data item
                fieldnames = data['data'][0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['data'])
            else:
                # Handle summary or comprehensive reports
                writer = csv.writer(csvfile)
                writer.writerow(['Report Type', data.get('report_type', 'Comprehensive Report')])
                writer.writerow(['Period', data.get('period', 'N/A')])
                # Add more CSV formatting as needed
    
    def _output_json(self, data, options):
        """Output report to JSON file"""
        
        with open(options['output_file'], 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)