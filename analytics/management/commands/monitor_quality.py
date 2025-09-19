"""
Management command for real-time quality monitoring and alerts
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
import time

from analytics.models import QualityScore, PerformanceMetrics
from vendors.models import VendorProfile
from bookings.models import Booking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Real-time monitoring system for quality scores and performance alerts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--monitor-duration',
            type=int,
            default=60,
            help='Duration to monitor in minutes (default: 60)',
        )
        parser.add_argument(
            '--check-interval',
            type=int,
            default=5,
            help='Check interval in minutes (default: 5)',
        )
        parser.add_argument(
            '--quality-threshold',
            type=float,
            default=70.0,
            help='Quality score threshold for alerts (default: 70.0)',
        )
        parser.add_argument(
            '--completion-threshold',
            type=float,
            default=80.0,
            help='Completion rate threshold for alerts (default: 80.0)',
        )
        parser.add_argument(
            '--rating-threshold',
            type=float,
            default=3.5,
            help='Average rating threshold for alerts (default: 3.5)',
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send email alerts for threshold violations',
        )
        parser.add_argument(
            '--alert-emails',
            type=str,
            nargs='+',
            help='Email addresses to send alerts to',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run monitoring without sending alerts',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        monitor_duration = options['monitor_duration']
        check_interval = options['check_interval']
        
        self.stdout.write(
            f"Starting real-time quality monitoring for {monitor_duration} minutes "
            f"(checking every {check_interval} minutes)"
        )
        
        # Monitoring thresholds
        thresholds = {
            'quality_score': options['quality_threshold'],
            'completion_rate': options['completion_threshold'],
            'rating': options['rating_threshold'],
        }
        
        self.stdout.write(f"Alert thresholds: {thresholds}")
        
        # Start monitoring loop
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=monitor_duration)
        check_count = 0
        alert_count = 0
        
        try:
            while timezone.now() < end_time:
                check_count += 1
                self.stdout.write(f"\n--- Check #{check_count} at {timezone.now().strftime('%H:%M:%S')} ---")
                
                # Perform quality checks
                alerts = self._perform_quality_checks(thresholds)
                
                if alerts:
                    alert_count += len(alerts)
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {len(alerts)} alert(s) detected!")
                    )
                    
                    for alert in alerts:
                        self.stdout.write(
                            self.style.ERROR(f"  • {alert['message']}")
                        )
                    
                    # Send alerts if enabled
                    if options['send_alerts'] and not options['dry_run']:
                        self._send_alerts(alerts, options['alert_emails'])
                    elif options['dry_run']:
                        self.stdout.write("  [DRY RUN] Would send alerts")
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✓ All vendors within acceptable thresholds")
                    )
                
                # Wait for next check
                if timezone.now() < end_time:
                    self.stdout.write(f"Waiting {check_interval} minutes for next check...")
                    time.sleep(check_interval * 60)
        
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring interrupted by user")
        
        # Summary
        duration = timezone.now() - start_time
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Monitoring Summary:")
        self.stdout.write(f"Duration: {duration}")
        self.stdout.write(f"Total checks performed: {check_count}")
        self.stdout.write(f"Total alerts generated: {alert_count}")
        self.stdout.write(f"Monitoring completed successfully!")
    
    def _perform_quality_checks(self, thresholds):
        """Perform quality checks and return alerts"""
        
        alerts = []
        
        # Check recent quality scores (last 7 days)
        recent_date = timezone.now().date() - timedelta(days=7)
        recent_scores = QualityScore.objects.filter(
            calculated_at__date__gte=recent_date
        ).select_related('vendor')
        
        for score in recent_scores:
            # Quality score threshold check
            if score.overall_score < thresholds['quality_score']:
                alerts.append({
                    'type': 'quality_score',
                    'vendor': score.vendor,
                    'message': f"{score.vendor.business_name}: Quality score {score.overall_score:.1f}/100 below threshold {thresholds['quality_score']}",
                    'severity': 'high' if score.overall_score < thresholds['quality_score'] - 10 else 'medium',
                    'current_value': float(score.overall_score),
                    'threshold': thresholds['quality_score'],
                })
            
            # Rating threshold check
            if score.avg_rating < thresholds['rating']:
                alerts.append({
                    'type': 'rating',
                    'vendor': score.vendor,
                    'message': f"{score.vendor.business_name}: Average rating {score.avg_rating:.1f}★ below threshold {thresholds['rating']}★",
                    'severity': 'medium',
                    'current_value': float(score.avg_rating),
                    'threshold': thresholds['rating'],
                })
        
        # Check recent performance metrics (last 3 days)
        recent_metrics = PerformanceMetrics.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=3)
        ).select_related('vendor')
        
        # Aggregate metrics by vendor
        vendor_performance = {}
        for metric in recent_metrics:
            vendor_id = metric.vendor.id
            if vendor_id not in vendor_performance:
                vendor_performance[vendor_id] = {
                    'vendor': metric.vendor,
                    'total_accepted': 0,
                    'total_completed': 0,
                    'dates_count': 0,
                }
            
            vp = vendor_performance[vendor_id]
            vp['total_accepted'] += metric.bookings_accepted
            vp['total_completed'] += metric.bookings_completed
            vp['dates_count'] += 1
        
        # Check completion rates
        for vendor_id, vp in vendor_performance.items():
            if vp['total_accepted'] > 0:
                completion_rate = (vp['total_completed'] / vp['total_accepted']) * 100
                
                if completion_rate < thresholds['completion_rate']:
                    alerts.append({
                        'type': 'completion_rate',
                        'vendor': vp['vendor'],
                        'message': f"{vp['vendor'].business_name}: Completion rate {completion_rate:.1f}% below threshold {thresholds['completion_rate']}%",
                        'severity': 'high' if completion_rate < thresholds['completion_rate'] - 15 else 'medium',
                        'current_value': completion_rate,
                        'threshold': thresholds['completion_rate'],
                    })
        
        # Check for vendors with recent booking issues
        problem_bookings = Booking.objects.filter(
            created_at__date__gte=timezone.now().date() - timedelta(days=1),
            status__in=['cancelled', 'refunded']
        ).select_related('service__vendor')
        
        vendor_cancellations = {}
        for booking in problem_bookings:
            vendor = booking.service.vendor if hasattr(booking.service, 'vendor') else None
            if vendor:
                vendor_id = vendor.id
                if vendor_id not in vendor_cancellations:
                    vendor_cancellations[vendor_id] = {
                        'vendor': vendor,
                        'count': 0,
                    }
                vendor_cancellations[vendor_id]['count'] += 1
        
        # Alert if too many cancellations
        for vendor_id, vc in vendor_cancellations.items():
            if vc['count'] >= 3:  # 3 or more cancellations in 24 hours
                alerts.append({
                    'type': 'cancellations',
                    'vendor': vc['vendor'],
                    'message': f"{vc['vendor'].business_name}: {vc['count']} booking cancellations in the last 24 hours",
                    'severity': 'high',
                    'current_value': vc['count'],
                    'threshold': 3,
                })
        
        return alerts
    
    def _send_alerts(self, alerts, alert_emails):
        """Send email alerts"""
        
        if not alert_emails:
            self.stdout.write("No alert email addresses configured")
            return
        
        # Group alerts by severity
        high_alerts = [a for a in alerts if a.get('severity') == 'high']
        medium_alerts = [a for a in alerts if a.get('severity') == 'medium']
        
        # Prepare email content
        subject = f"Hawwa Platform Quality Alert - {len(alerts)} issue(s) detected"
        
        message_lines = [
            "Quality Monitoring Alert",
            "=" * 30,
            f"Alert generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total alerts: {len(alerts)}",
            ""
        ]
        
        if high_alerts:
            message_lines.extend([
                "HIGH PRIORITY ALERTS:",
                "-" * 20
            ])
            for alert in high_alerts:
                message_lines.append(f"• {alert['message']}")
            message_lines.append("")
        
        if medium_alerts:
            message_lines.extend([
                "MEDIUM PRIORITY ALERTS:",
                "-" * 22
            ])
            for alert in medium_alerts:
                message_lines.append(f"• {alert['message']}")
            message_lines.append("")
        
        message_lines.extend([
            "Please review the vendor performance and take appropriate action.",
            "",
            "This is an automated alert from the Hawwa Quality Monitoring System."
        ])
        
        message = "\n".join(message_lines)
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hawwa.com'),
                recipient_list=alert_emails,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ Alert email sent to {len(alert_emails)} recipient(s)")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to send alert email: {str(e)}")
            )
            logger.error(f"Failed to send quality alert email: {str(e)}")