"""
Management command to calculate quality scores for all vendors
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

from analytics.services import QualityScoringEngine
from vendors.models import VendorProfile
from analytics.models import QualityScore

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate quality scores for vendors based on their performance metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Calculate score for specific vendor ID',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation even if score exists for the period',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output with detailed scoring breakdown',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without saving results',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Initialize scoring engine
        scoring_engine = QualityScoringEngine()
        
        # Determine date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=options['days'])
        
        self.stdout.write(
            f"Calculating quality scores for period: {start_date} to {end_date}"
        )
        
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
        
        # Process vendors
        total_processed = 0
        total_updated = 0
        total_errors = 0
        
        for vendor in vendors:
            try:
                # Check if score already exists for this period
                existing_score = QualityScore.objects.filter(
                    vendor=vendor,
                    period_start=start_date,
                    period_end=end_date
                ).first()
                
                if existing_score and not options['force']:
                    if options['verbose']:
                        self.stdout.write(
                            f"Skipping {vendor.business_name} - score already exists for this period"
                        )
                    continue
                
                # Calculate quality score
                quality_score = scoring_engine.calculate_quality_score(
                    vendor=vendor,
                    period_start=start_date,
                    period_end=end_date
                )
                
                if options['verbose']:
                    self._print_score_breakdown(vendor, quality_score)
                
                # The scoring engine already saves the score, so we just need to track success
                if not options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Quality score calculated for {vendor.business_name}: {quality_score.overall_score:.1f}/100"
                        )
                    )
                    total_updated += 1
                else:
                    self.stdout.write(
                        f"[DRY RUN] Would calculate score for {vendor.business_name}: {quality_score.overall_score:.1f}/100"
                    )
                
                total_processed += 1
                
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error processing {vendor.business_name}: {str(e)}"
                    )
                )
                logger.error(f"Error calculating quality score for vendor {vendor.id}: {str(e)}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Quality Score Calculation Summary:")
        self.stdout.write(f"Total vendors processed: {total_processed}")
        if not options['dry_run']:
            self.stdout.write(f"Scores updated/created: {total_updated}")
        self.stdout.write(f"Errors encountered: {total_errors}")
        
        # Calculate rankings if scores were updated
        if total_updated > 0 and not options['dry_run']:
            self.stdout.write("\nCalculating vendor rankings...")
            try:
                ranking_engine = scoring_engine
                ranking_engine.calculate_vendor_rankings(
                    period_start=start_date,
                    period_end=end_date
                )
                self.stdout.write(
                    self.style.SUCCESS("✓ Vendor rankings updated successfully")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error updating rankings: {str(e)}")
                )
        
        # Award certifications if scores were updated
        if total_updated > 0 and not options['dry_run']:
            self.stdout.write("\nAwarding quality certifications...")
            try:
                awarded_count = scoring_engine.award_quality_certifications(
                    period_start=start_date,
                    period_end=end_date
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {awarded_count} quality certifications awarded")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error awarding certifications: {str(e)}")
                )
    
    def _print_score_breakdown(self, vendor, quality_score):
        """Print detailed score breakdown for verbose mode"""
        self.stdout.write(f"\n{vendor.business_name} Score Breakdown:")
        self.stdout.write(f"  Overall Score: {quality_score.overall_score:.1f}/100")
        self.stdout.write(f"  Customer Ratings: {quality_score.customer_ratings_score:.1f}/100")
        self.stdout.write(f"  Completion Rate: {quality_score.completion_rate_score:.1f}/100")
        self.stdout.write(f"  Response Time: {quality_score.response_time_score:.1f}/100")
        self.stdout.write(f"  Repeat Customers: {quality_score.repeat_customers_score:.1f}/100")
        self.stdout.write(f"  Performance Trends: {quality_score.performance_trends_score:.1f}/100")
        self.stdout.write(f"  Metrics: {quality_score.total_bookings} bookings, {quality_score.avg_rating:.1f}★ rating")