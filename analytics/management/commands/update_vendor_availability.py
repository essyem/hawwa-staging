"""
Management command to update vendor availability and workload data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from vendors.models import VendorProfile
from bookings.models import Booking
from analytics.assignment_models import VendorAvailability, VendorWorkload
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update vendor availability and workload metrics for assignment system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Specific vendor ID to update'
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=30,
            help='Number of days ahead to generate availability (default: 30)'
        )
        parser.add_argument(
            '--reset-workload',
            action='store_true',
            help='Reset and recalculate all workload metrics'
        )
    
    def handle(self, *args, **options):
        vendor_id = options.get('vendor_id')
        days_ahead = options.get('days_ahead')
        reset_workload = options.get('reset_workload')
        
        self.stdout.write(
            self.style.SUCCESS('Starting vendor availability and workload update...')
        )
        
        # Get vendors to update
        if vendor_id:
            vendors = VendorProfile.objects.filter(id=vendor_id, status='active')
            if not vendors.exists():
                self.stdout.write(
                    self.style.ERROR(f'Vendor with ID {vendor_id} not found or not active')
                )
                return
        else:
            vendors = VendorProfile.objects.filter(status='active', verified=True)
        
        self.stdout.write(f'Updating {vendors.count()} vendors...')
        
        updated_availability = 0
        updated_workload = 0
        errors = 0
        
        for vendor in vendors:
            try:
                self.stdout.write(f'Processing vendor: {vendor.business_name}')
                
                # Update availability
                availability_created = self._update_vendor_availability(vendor, days_ahead)
                updated_availability += availability_created
                
                # Update workload
                workload_updated = self._update_vendor_workload(vendor, reset_workload)
                if workload_updated:
                    updated_workload += 1
                
                self.stdout.write(f'  ✓ Created {availability_created} availability slots')
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error updating vendor {vendor.business_name}: {str(e)}')
                )
                logger.error(f'Error updating vendor {vendor.id}: {str(e)}', exc_info=True)
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('UPDATE SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Vendors processed: {vendors.count()}')
        self.stdout.write(f'Availability slots created: {updated_availability}')
        self.stdout.write(f'Workload records updated: {updated_workload}')
        self.stdout.write(f'Errors encountered: {errors}')
    
    def _update_vendor_availability(self, vendor: VendorProfile, days_ahead: int) -> int:
        """Update vendor availability for upcoming days."""
        created_count = 0
        
        # Generate availability for next N days
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_ahead)
        
        current_date = start_date
        while current_date <= end_date:
            # Check if availability already exists for this date
            existing = VendorAvailability.objects.filter(
                vendor=vendor,
                date=current_date
            ).exists()
            
            if not existing:
                # Create default availability (9 AM to 5 PM, available)
                # In production, this would be based on vendor preferences
                availability = VendorAvailability.objects.create(
                    vendor=vendor,
                    date=current_date,
                    start_time=datetime.strptime('09:00', '%H:%M').time(),
                    end_time=datetime.strptime('17:00', '%H:%M').time(),
                    status='available',
                    max_concurrent_bookings=3,  # Default capacity
                    current_bookings=0
                )
                created_count += 1
            
            current_date += timedelta(days=1)
        
        return created_count
    
    def _update_vendor_workload(self, vendor: VendorProfile, reset: bool = False) -> bool:
        """Update vendor workload metrics."""
        try:
            workload, created = VendorWorkload.objects.get_or_create(
                vendor=vendor,
                defaults={
                    'daily_booking_limit': 5,
                    'weekly_booking_limit': 30,
                    'monthly_booking_limit': 120,
                    'preferred_service_radius_km': 25,
                }
            )
            
            if reset or created:
                # Calculate current metrics from actual bookings
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
                
                # Active bookings (confirmed, in progress)
                active_bookings = Booking.objects.filter(
                    # This would need to be updated based on actual vendor assignment field
                    status__in=['confirmed', 'in_progress'],
                    start_date__gte=today
                ).count()
                
                # Pending bookings
                pending_bookings = Booking.objects.filter(
                    status='pending',
                    start_date__gte=today
                ).count()
                
                # Today's completed bookings
                completed_today = Booking.objects.filter(
                    status='completed',
                    start_date=today
                ).count()
                
                # Update workload metrics
                workload.active_bookings = active_bookings
                workload.pending_bookings = pending_bookings
                workload.completed_today = completed_today
                
                # Calculate performance metrics (last 7 days)
                week_ago = today - timedelta(days=7)
                
                # This would need actual vendor assignment relationships
                # For now, using placeholder logic
                workload.avg_response_time_minutes = 45  # Default
                workload.completion_rate_7days = 95.0  # Default
                workload.customer_satisfaction_7days = 4.5  # Default
                
                # Update workload status
                workload.update_workload_status()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f'Error updating workload for vendor {vendor.id}: {str(e)}')
            raise