"""
Management command to auto-assign vendors to pending bookings
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from bookings.models import Booking
from analytics.assignment_service import smart_assignment_engine
from analytics.assignment_models import VendorAssignment
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-assign vendors to pending bookings using AI scoring'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--booking-id',
            type=str,
            help='Specific booking ID to process'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=float,
            default=0.7,
            help='Minimum confidence threshold for auto-assignment (default: 0.7)'
        )
        parser.add_argument(
            '--max-bookings',
            type=int,
            default=50,
            help='Maximum number of bookings to process (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be assigned without making changes'
        )
    
    def handle(self, *args, **options):
        booking_id = options.get('booking_id')
        confidence_threshold = options.get('confidence_threshold')
        max_bookings = options.get('max_bookings')
        dry_run = options.get('dry_run')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting vendor auto-assignment process...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No assignments will be created')
            )
        
        # Get pending bookings that need vendor assignment
        if booking_id:
            bookings = Booking.objects.filter(
                booking_number=booking_id,
                status__in=['pending', 'confirmed']
            )
            if not bookings.exists():
                raise CommandError(f'Booking {booking_id} not found or not eligible for assignment')
        else:
            # Get bookings without vendor assignments
            bookings = Booking.objects.filter(
                status__in=['pending', 'confirmed']
            ).exclude(
                vendor_assignments__status__in=['accepted', 'auto_assigned']
            )[:max_bookings]
        
        if not bookings.exists():
            self.stdout.write(
                self.style.WARNING('No eligible bookings found for assignment')
            )
            return
        
        self.stdout.write(f'Found {bookings.count()} bookings to process')
        
        assigned_count = 0
        recommendation_count = 0
        error_count = 0
        
        for booking in bookings:
            try:
                self.stdout.write(f'Processing booking {booking.booking_number}...')
                
                # Get vendor recommendations
                vendor_recommendations = smart_assignment_engine.find_best_vendors(
                    booking, max_vendors=5
                )
                
                if not vendor_recommendations:
                    self.stdout.write(
                        self.style.WARNING(f'  No vendor recommendations for booking {booking.booking_number}')
                    )
                    continue
                
                best_vendor_data = vendor_recommendations[0]
                confidence = best_vendor_data['confidence_level']
                
                self.stdout.write(
                    f'  Best vendor: {best_vendor_data["vendor"].business_name} '
                    f'(Score: {best_vendor_data["total_score"]}, Confidence: {confidence})'
                )
                
                # Show all recommendations
                for i, vendor_data in enumerate(vendor_recommendations, 1):
                    vendor = vendor_data['vendor']
                    score = vendor_data['total_score']
                    self.stdout.write(f'    {i}. {vendor.business_name} - Score: {score}')
                
                recommendation_count += 1
                
                # Auto-assign if confidence is high enough
                if confidence >= confidence_threshold:
                    if not dry_run:
                        assignment = smart_assignment_engine.auto_assign_vendor(booking, confidence_threshold)
                        if assignment:
                            assigned_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Auto-assigned to {assignment.vendor.business_name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  ✗ Auto-assignment failed')
                            )
                    else:
                        assigned_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Would auto-assign to {best_vendor_data["vendor"].business_name}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ! Confidence {confidence} below threshold {confidence_threshold}')
                    )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing booking {booking.booking_number}: {str(e)}')
                )
                logger.error(f'Error in auto-assignment command: {str(e)}', exc_info=True)
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('AUTO-ASSIGNMENT SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Bookings processed: {bookings.count()}')
        self.stdout.write(f'Recommendations generated: {recommendation_count}')
        self.stdout.write(f'Auto-assignments created: {assigned_count}')
        self.stdout.write(f'Errors encountered: {error_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run - no actual assignments were created')
            )
        
        success_rate = (assigned_count / bookings.count() * 100) if bookings.count() > 0 else 0
        self.stdout.write(f'Success rate: {success_rate:.1f}%')
        
        if success_rate >= 80:
            self.stdout.write(self.style.SUCCESS('✓ Excellent assignment rate!'))
        elif success_rate >= 60:
            self.stdout.write(self.style.WARNING('! Good assignment rate, some improvements possible'))
        else:
            self.stdout.write(self.style.ERROR('✗ Low assignment rate, review assignment criteria'))