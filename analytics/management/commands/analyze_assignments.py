"""
Management command to analyze assignment performance and generate insights
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from datetime import datetime, timedelta
from analytics.assignment_models import VendorAssignment, AssignmentLog
from analytics.assignment_service import smart_assignment_engine
import json

class Command(BaseCommand):
    help = 'Analyze vendor assignment performance and generate insights'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        parser.add_argument(
            '--export-json',
            type=str,
            help='Export analysis to JSON file'
        )
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Analyze specific vendor performance'
        )
    
    def handle(self, *args, **options):
        days = options.get('days')
        export_file = options.get('export_json')
        vendor_id = options.get('vendor_id')
        
        self.stdout.write(
            self.style.SUCCESS(f'Analyzing assignment performance for last {days} days...')
        )
        
        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset
        assignments = VendorAssignment.objects.filter(
            assigned_at__range=[start_date, end_date]
        )
        
        if vendor_id:
            assignments = assignments.filter(vendor_id=vendor_id)
            self.stdout.write(f'Filtering for vendor ID: {vendor_id}')
        
        # Generate analysis
        analysis = self._generate_analysis(assignments, start_date, end_date)
        
        # Display results
        self._display_analysis(analysis)
        
        # Export if requested
        if export_file:
            self._export_analysis(analysis, export_file)
            self.stdout.write(
                self.style.SUCCESS(f'Analysis exported to {export_file}')
            )
    
    def _generate_analysis(self, assignments, start_date, end_date):
        """Generate comprehensive assignment analysis."""
        
        analysis = {
            'period': {
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'days': (end_date.date() - start_date.date()).days
            },
            'overall_metrics': {},
            'assignment_methods': {},
            'response_times': {},
            'score_distribution': {},
            'vendor_performance': {},
            'confidence_analysis': {},
            'recommendations': []
        }
        
        # Overall metrics
        total_assignments = assignments.count()
        accepted_assignments = assignments.filter(status='accepted').count()
        declined_assignments = assignments.filter(status='declined').count()
        auto_assignments = assignments.filter(assignment_method='smart_ai').count()
        
        analysis['overall_metrics'] = {
            'total_assignments': total_assignments,
            'accepted_assignments': accepted_assignments,
            'declined_assignments': declined_assignments,
            'auto_assignments': auto_assignments,
            'acceptance_rate': round((accepted_assignments / total_assignments * 100) if total_assignments > 0 else 0, 1),
            'auto_assignment_rate': round((auto_assignments / total_assignments * 100) if total_assignments > 0 else 0, 1)
        }
        
        # Assignment methods breakdown
        method_stats = assignments.values('assignment_method').annotate(
            count=Count('id'),
            avg_score=Avg('total_score'),
            acceptance_rate=Count('id', filter=Q(status='accepted')) * 100.0 / Count('id')
        )
        
        analysis['assignment_methods'] = {
            method['assignment_method']: {
                'count': method['count'],
                'avg_score': round(float(method['avg_score'] or 0), 1),
                'acceptance_rate': round(float(method['acceptance_rate'] or 0), 1)
            }
            for method in method_stats
        }
        
        # Response times
        responded_assignments = assignments.filter(
            vendor_response_time_minutes__isnull=False
        )
        
        if responded_assignments.exists():
            avg_response_time = responded_assignments.aggregate(
                avg=Avg('vendor_response_time_minutes')
            )['avg']
            
            analysis['response_times'] = {
                'average_minutes': round(float(avg_response_time or 0), 1),
                'fast_responses': responded_assignments.filter(vendor_response_time_minutes__lte=30).count(),
                'slow_responses': responded_assignments.filter(vendor_response_time_minutes__gt=120).count(),
                'total_responses': responded_assignments.count()
            }
        
        # Score distribution
        score_ranges = [
            (90, 100, 'excellent'),
            (80, 89, 'good'),
            (70, 79, 'average'),
            (60, 69, 'below_average'),
            (0, 59, 'poor')
        ]
        
        for min_score, max_score, label in score_ranges:
            count = assignments.filter(
                total_score__gte=min_score,
                total_score__lte=max_score
            ).count()
            analysis['score_distribution'][label] = count
        
        # Vendor performance (top 10)
        vendor_stats = assignments.values('vendor__business_name').annotate(
            assignment_count=Count('id'),
            acceptance_rate=Count('id', filter=Q(status='accepted')) * 100.0 / Count('id'),
            avg_score=Avg('total_score'),
            avg_response_time=Avg('vendor_response_time_minutes')
        ).order_by('-assignment_count')[:10]
        
        analysis['vendor_performance'] = [
            {
                'vendor_name': vendor['vendor__business_name'],
                'assignments': vendor['assignment_count'],
                'acceptance_rate': round(float(vendor['acceptance_rate'] or 0), 1),
                'avg_score': round(float(vendor['avg_score'] or 0), 1),
                'avg_response_time': round(float(vendor['avg_response_time'] or 0), 1)
            }
            for vendor in vendor_stats
        ]
        
        # Confidence analysis
        high_confidence = assignments.filter(confidence_level__gte=0.8).count()
        medium_confidence = assignments.filter(
            confidence_level__gte=0.6, confidence_level__lt=0.8
        ).count()
        low_confidence = assignments.filter(confidence_level__lt=0.6).count()
        
        analysis['confidence_analysis'] = {
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'avg_confidence': round(float(assignments.aggregate(avg=Avg('confidence_level'))['avg'] or 0), 2)
        }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Acceptance rate recommendations
        acceptance_rate = analysis['overall_metrics']['acceptance_rate']
        if acceptance_rate < 70:
            recommendations.append({
                'type': 'acceptance_rate',
                'priority': 'high',
                'message': f'Low acceptance rate ({acceptance_rate}%). Review vendor scoring criteria and availability data.',
                'action': 'Improve vendor filtering and scoring algorithms'
            })
        
        # Auto-assignment rate recommendations
        auto_rate = analysis['overall_metrics']['auto_assignment_rate']
        if auto_rate < 60:
            recommendations.append({
                'type': 'automation',
                'priority': 'medium',
                'message': f'Low auto-assignment rate ({auto_rate}%). Consider lowering confidence threshold.',
                'action': 'Review confidence thresholds and improve data quality'
            })
        
        # Response time recommendations
        if 'response_times' in analysis:
            avg_response = analysis['response_times']['average_minutes']
            if avg_response > 60:
                recommendations.append({
                    'type': 'response_time',
                    'priority': 'medium',
                    'message': f'Average response time is {avg_response} minutes. Target vendors with faster response rates.',
                    'action': 'Prioritize vendors with better response time history'
                })
        
        # Confidence recommendations
        avg_confidence = analysis['confidence_analysis']['avg_confidence']
        if avg_confidence < 0.7:
            recommendations.append({
                'type': 'confidence',
                'priority': 'medium',
                'message': f'Average confidence level is {avg_confidence}. Improve data completeness.',
                'action': 'Enhance vendor availability and workload data collection'
            })
        
        return recommendations
    
    def _display_analysis(self, analysis):
        """Display analysis results in a formatted way."""
        
        # Overall metrics
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('ASSIGNMENT PERFORMANCE ANALYSIS'))
        self.stdout.write('='*60)
        
        metrics = analysis['overall_metrics']
        self.stdout.write(f"Period: {analysis['period']['start_date']} to {analysis['period']['end_date']}")
        self.stdout.write(f"Total Assignments: {metrics['total_assignments']}")
        self.stdout.write(f"Acceptance Rate: {metrics['acceptance_rate']}%")
        self.stdout.write(f"Auto-Assignment Rate: {metrics['auto_assignment_rate']}%")
        
        # Assignment methods
        self.stdout.write('\n' + '-'*40)
        self.stdout.write(self.style.SUCCESS('ASSIGNMENT METHODS'))
        self.stdout.write('-'*40)
        
        for method, stats in analysis['assignment_methods'].items():
            self.stdout.write(f"{method.replace('_', ' ').title()}:")
            self.stdout.write(f"  Count: {stats['count']}")
            self.stdout.write(f"  Avg Score: {stats['avg_score']}")
            self.stdout.write(f"  Acceptance Rate: {stats['acceptance_rate']}%")
        
        # Response times
        if 'response_times' in analysis:
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(self.style.SUCCESS('RESPONSE TIMES'))
            self.stdout.write('-'*40)
            
            response = analysis['response_times']
            self.stdout.write(f"Average Response Time: {response['average_minutes']} minutes")
            self.stdout.write(f"Fast Responses (≤30 min): {response['fast_responses']}")
            self.stdout.write(f"Slow Responses (>2 hours): {response['slow_responses']}")
        
        # Score distribution
        self.stdout.write('\n' + '-'*40)
        self.stdout.write(self.style.SUCCESS('SCORE DISTRIBUTION'))
        self.stdout.write('-'*40)
        
        for category, count in analysis['score_distribution'].items():
            self.stdout.write(f"{category.replace('_', ' ').title()}: {count}")
        
        # Top vendors
        if analysis['vendor_performance']:
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(self.style.SUCCESS('TOP VENDOR PERFORMANCE'))
            self.stdout.write('-'*40)
            
            for i, vendor in enumerate(analysis['vendor_performance'][:5], 1):
                self.stdout.write(f"{i}. {vendor['vendor_name']}")
                self.stdout.write(f"   Assignments: {vendor['assignments']}")
                self.stdout.write(f"   Acceptance Rate: {vendor['acceptance_rate']}%")
                self.stdout.write(f"   Avg Score: {vendor['avg_score']}")
        
        # Recommendations
        if analysis['recommendations']:
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(self.style.WARNING('RECOMMENDATIONS'))
            self.stdout.write('-'*40)
            
            for rec in analysis['recommendations']:
                priority_style = self.style.ERROR if rec['priority'] == 'high' else self.style.WARNING
                self.stdout.write(priority_style(f"[{rec['priority'].upper()}] {rec['message']}"))
                self.stdout.write(f"Action: {rec['action']}\n")
    
    def _export_analysis(self, analysis, filename):
        """Export analysis to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error exporting analysis: {str(e)}')
            )