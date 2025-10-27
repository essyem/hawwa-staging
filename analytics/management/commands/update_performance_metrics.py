"""
Management command to update performance metrics for all vendors
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

from analytics.models import PerformanceMetrics
from vendors.models import VendorProfile
from bookings.models import Booking
from services.models import ServiceReview

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update performance metrics for vendors based on their booking and review data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Update metrics for specific vendor ID',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to update (YYYY-MM-DD format). Default: yesterday',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to update (default: 1)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if metrics exist for the date',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output with detailed metrics',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Determine date to process
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError("Date must be in YYYY-MM-DD format")
        else:
            target_date = timezone.now().date() - timedelta(days=1)  # Yesterday
        
        # Process multiple days if specified
        dates_to_process = []
        for i in range(options['days_back']):
            dates_to_process.append(target_date - timedelta(days=i))
        
        self.stdout.write(f"Processing performance metrics for dates: {dates_to_process}")
        
        # Get vendors to process
        if options['vendor_id']:
            try:
                vendors = [VendorProfile.objects.get(id=options['vendor_id'])]
                self.stdout.write(f"Processing vendor ID: {options['vendor_id']}")
            except VendorProfile.DoesNotExist:
                raise CommandError(f"Vendor with ID {options['vendor_id']} does not exist")
        else:
            vendors = VendorProfile.objects.filter(
                status='active',
                verified=True
            ).select_related('user')
            self.stdout.write(f"Processing {vendors.count()} active vendors")
        
        # Process each date
        total_processed = 0
        total_updated = 0
        total_errors = 0
        
        for process_date in dates_to_process:
            self.stdout.write(f"\nProcessing date: {process_date}")
            
            for vendor in vendors:
                try:
                    # Check if metrics already exist for this date
                    existing_metrics = PerformanceMetrics.objects.filter(
                        vendor=vendor,
                        date=process_date
                    ).first()
                    
                    if existing_metrics and not options['force']:
                        if options['verbose']:
                            self.stdout.write(
                                f"Skipping {vendor.business_name} - metrics already exist for {process_date}"
                            )
                        continue
                    
                    # Calculate metrics for this vendor and date
                    metrics_data = self._calculate_vendor_metrics(vendor, process_date)
                    
                    if options['verbose']:
                        self._print_metrics_breakdown(vendor, process_date, metrics_data)
                    
                    # Save or update metrics
                    performance_metrics, created = PerformanceMetrics.objects.update_or_create(
                        vendor=vendor,
                        date=process_date,
                        defaults=metrics_data
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Created metrics for {vendor.business_name} on {process_date}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Updated metrics for {vendor.business_name} on {process_date}"
                            )
                        )
                    total_updated += 1
                    total_processed += 1
                    
                except Exception as e:
                    total_errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Error processing {vendor.business_name} for {process_date}: {str(e)}"
                        )
                    )
                    logger.error(f"Error calculating metrics for vendor {vendor.id} on {process_date}: {str(e)}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Performance Metrics Update Summary:")
        self.stdout.write(f"Total vendor-date combinations processed: {total_processed}")
        self.stdout.write(f"Metrics updated/created: {total_updated}")
        self.stdout.write(f"Errors encountered: {total_errors}")
    
    def _calculate_vendor_metrics(self, vendor, target_date):
        """Calculate performance metrics for a vendor on a specific date"""
        
        # Date range for the day
        start_datetime_naive = datetime.combine(target_date, datetime.min.time())
        end_datetime_naive = datetime.combine(target_date, datetime.max.time())
        start_datetime = timezone.make_aware(start_datetime_naive)
        end_datetime = timezone.make_aware(end_datetime_naive)
        
        # Booking metrics for the day
        bookings_qs = Booking.objects.filter(
            service__vendor_profile=vendor,
            created_at__range=[start_datetime, end_datetime]
        )
        
        bookings_received = bookings_qs.count()
        bookings_accepted = bookings_qs.filter(
            status__in=['confirmed', 'in_progress', 'completed']
        ).count()
        bookings_completed = bookings_qs.filter(status='completed').count()
        bookings_cancelled = bookings_qs.filter(status='cancelled').count()
        bookings_no_show = bookings_qs.filter(
            Q(status='cancelled') & Q(notes__icontains='no show')
        ).count()
        
        # Revenue calculation
        completed_bookings = bookings_qs.filter(status='completed')
        revenue = completed_bookings.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        # Average booking value
        avg_booking_value = revenue / bookings_completed if bookings_completed > 0 else Decimal('0.00')
        
        # Customer metrics
        unique_customers = bookings_qs.values('user').distinct().count()
        
        # Calculate repeat customers (customers who have booked before this date)
        repeat_customers = 0
        for booking in bookings_qs:
            previous_bookings = Booking.objects.filter(
                service__vendor_profile=vendor,
                user=booking.user,
                created_at__lt=start_datetime
            ).exists()
            if previous_bookings:
                repeat_customers += 1
        
        # Ratings for the day (reviews created on this date)
        reviews_qs = ServiceReview.objects.filter(
            service__vendor_profile=vendor,
            created_at__range=[start_datetime, end_datetime]
        )
        
        total_ratings = reviews_qs.count()
        avg_rating = reviews_qs.aggregate(avg=Avg('rating'))['avg'] or Decimal('0.00')
        
        # Rating distribution
        five_star = reviews_qs.filter(rating=5).count()
        four_star = reviews_qs.filter(rating=4).count()
        three_star = reviews_qs.filter(rating=3).count()
        two_star = reviews_qs.filter(rating=2).count()
        one_star = reviews_qs.filter(rating=1).count()
        
        # Response time calculation (simplified - would need actual response tracking)
        # For now, using a default based on vendor's typical response time
        avg_response_time_minutes = 120  # Default 2 hours, should be calculated from actual data
        
        # First response rate (simplified)
        first_response_rate = Decimal('85.0')  # Default, should be calculated from actual data
        
        # On-time completion rate (simplified)
        on_time_completion_rate = Decimal('90.0')  # Default, should be calculated from actual data
        
        # Rework rate (simplified)
        rework_rate = Decimal('5.0')  # Default, should be calculated from actual data
        
        return {
            'bookings_received': bookings_received,
            'bookings_accepted': bookings_accepted,
            'bookings_completed': bookings_completed,
            'bookings_cancelled': bookings_cancelled,
            'bookings_no_show': bookings_no_show,
            'avg_response_time_minutes': avg_response_time_minutes,
            'first_response_rate': first_response_rate,
            'total_ratings': total_ratings,
            'avg_rating': avg_rating,
            'five_star_ratings': five_star,
            'four_star_ratings': four_star,
            'three_star_ratings': three_star,
            'two_star_ratings': two_star,
            'one_star_ratings': one_star,
            'revenue': revenue,
            'commission_paid': revenue * Decimal('0.15'),  # Assume 15% commission
            'avg_booking_value': avg_booking_value,
            'new_customers': unique_customers - repeat_customers,
            'repeat_customers': repeat_customers,
            'total_unique_customers': unique_customers,
            'on_time_completion_rate': on_time_completion_rate,
            'rework_rate': rework_rate,
        }
    
    def _print_metrics_breakdown(self, vendor, date, metrics_data):
        """Print detailed metrics breakdown for verbose mode"""
        self.stdout.write(f"\n{vendor.business_name} Metrics for {date}:")
        self.stdout.write(f"  Bookings: {metrics_data['bookings_received']} received, {metrics_data['bookings_completed']} completed")
        self.stdout.write(f"  Revenue: ${metrics_data['revenue']:.2f}")
        self.stdout.write(f"  Ratings: {metrics_data['total_ratings']} reviews, {metrics_data['avg_rating']:.1f}★ average")
        self.stdout.write(f"  Customers: {metrics_data['total_unique_customers']} total, {metrics_data['repeat_customers']} repeat")