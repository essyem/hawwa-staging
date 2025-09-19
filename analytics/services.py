"""
Quality Scoring Engine for Hawwa Platform
Automated quality scoring system with multi-factor analysis
"""

from django.db.models import Q, Avg, Count, F, Case, When, FloatField, Sum
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
import json

from .models import QualityScore, PerformanceMetrics, VendorRanking, QualityCertification
from vendors.models import VendorProfile, VendorAnalytics
from bookings.models import Booking
from services.models import ServiceReview

logger = logging.getLogger(__name__)


class QualityScoringEngine:
    """
    AI-powered quality scoring engine that analyzes:
    - Customer ratings and reviews
    - Booking completion rates
    - Response times
    - Repeat customer rates
    - Performance trends over time
    """
    
    def __init__(self):
        # Default weights for scoring components
        self.default_weights = {
            'customer_ratings': 0.30,      # 30% - Customer satisfaction
            'completion_rate': 0.25,       # 25% - Reliability
            'response_time': 0.20,         # 20% - Responsiveness
            'repeat_customers': 0.15,      # 15% - Customer loyalty
            'performance_trends': 0.10,    # 10% - Improvement over time
        }
        
        # Scoring thresholds
        self.thresholds = {
            'excellent_rating': 4.5,       # 4.5+ stars = excellent
            'good_rating': 4.0,            # 4.0+ stars = good
            'acceptable_rating': 3.5,      # 3.5+ stars = acceptable
            'fast_response_hours': 2,      # < 2 hours = fast response
            'good_response_hours': 6,      # < 6 hours = good response
            'excellent_completion': 95,    # 95%+ = excellent
            'good_completion': 85,         # 85%+ = good
            'high_repeat_rate': 60,        # 60%+ repeat customers = high
            'good_repeat_rate': 40,        # 40%+ repeat customers = good
        }
    
    def calculate_quality_score(self, vendor, period_start=None, period_end=None, weights=None):
        """
        Calculate comprehensive quality score for a vendor
        
        Args:
            vendor: VendorProfile instance
            period_start: Start date for analysis (default: 90 days ago)
            period_end: End date for analysis (default: today)
            weights: Custom weights dict (default: self.default_weights)
            
        Returns:
            QualityScore instance
        """
        
        # Set default period if not provided
        if not period_end:
            period_end = timezone.now().date()
        if not period_start:
            period_start = period_end - timedelta(days=90)
        
        # Use default weights if not provided
        if not weights:
            weights = self.default_weights.copy()
        
        logger.info(f"Calculating quality score for {vendor.business_name} from {period_start} to {period_end}")
        
        # Calculate individual component scores
        customer_ratings_score = self._calculate_customer_ratings_score(vendor, period_start, period_end)
        completion_rate_score = self._calculate_completion_rate_score(vendor, period_start, period_end)
        response_time_score = self._calculate_response_time_score(vendor, period_start, period_end)
        repeat_customers_score = self._calculate_repeat_customers_score(vendor, period_start, period_end)
        performance_trends_score = self._calculate_performance_trends_score(vendor, period_start, period_end)
        
        # Calculate weighted overall score
        overall_score = (
            customer_ratings_score * weights['customer_ratings'] +
            completion_rate_score * weights['completion_rate'] +
            response_time_score * weights['response_time'] +
            repeat_customers_score * weights['repeat_customers'] +
            performance_trends_score * weights['performance_trends']
        )
        
        # Get supporting metrics
        metrics = self._get_vendor_metrics(vendor, period_start, period_end)
        
        # Create or update quality score record
        quality_score, created = QualityScore.objects.update_or_create(
            vendor=vendor,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'overall_score': round(overall_score, 2),
                'customer_ratings_score': round(customer_ratings_score, 2),
                'completion_rate_score': round(completion_rate_score, 2),
                'response_time_score': round(response_time_score, 2),
                'repeat_customers_score': round(repeat_customers_score, 2),
                'performance_trends_score': round(performance_trends_score, 2),
                'weights': weights,
                'total_bookings': metrics['total_bookings'],
                'completed_bookings': metrics['completed_bookings'],
                'avg_rating': metrics['avg_rating'],
                'avg_response_time_hours': metrics['avg_response_time_hours'],
                'repeat_customer_rate': metrics['repeat_customer_rate'],
                'trend_direction': metrics['trend_direction'],
            }
        )
        
        logger.info(f"Quality score calculated: {overall_score:.2f}/100 for {vendor.business_name}")
        
        return quality_score
    
    def _calculate_customer_ratings_score(self, vendor, period_start, period_end):
        """Calculate score based on customer ratings and reviews"""
        
        # Get bookings and reviews in the period
        bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            created_at__date__range=[period_start, period_end],
            status='completed'
        )
        
        if not bookings.exists():
            return 0
        
        # Get average rating from service reviews
        reviews = ServiceReview.objects.filter(
            service__vendor_profile=vendor,
            created_at__date__range=[period_start, period_end]
        )
        
        if not reviews.exists():
            return 50  # Neutral score if no reviews
        
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Convert rating to 0-100 score
        if avg_rating >= self.thresholds['excellent_rating']:
            score = 90 + ((avg_rating - self.thresholds['excellent_rating']) / 0.5) * 10
        elif avg_rating >= self.thresholds['good_rating']:
            score = 75 + ((avg_rating - self.thresholds['good_rating']) / 0.5) * 15
        elif avg_rating >= self.thresholds['acceptable_rating']:
            score = 60 + ((avg_rating - self.thresholds['acceptable_rating']) / 0.5) * 15
        else:
            score = (avg_rating / self.thresholds['acceptable_rating']) * 60
        
        return min(100, max(0, score))
    
    def _calculate_completion_rate_score(self, vendor, period_start, period_end):
        """Calculate score based on booking completion rate"""
        
        bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            created_at__date__range=[period_start, period_end]
        ).exclude(status__in=['draft', 'pending'])
        
        if not bookings.exists():
            return 0
        
        total_bookings = bookings.count()
        completed_bookings = bookings.filter(status='completed').count()
        
        completion_rate = (completed_bookings / total_bookings) * 100
        
        # Convert completion rate to 0-100 score
        if completion_rate >= self.thresholds['excellent_completion']:
            score = 90 + ((completion_rate - self.thresholds['excellent_completion']) / 5) * 10
        elif completion_rate >= self.thresholds['good_completion']:
            score = 75 + ((completion_rate - self.thresholds['good_completion']) / 10) * 15
        else:
            score = (completion_rate / self.thresholds['good_completion']) * 75
        
        return min(100, max(0, score))
    
    def _calculate_response_time_score(self, vendor, period_start, period_end):
        """Calculate score based on average response time"""
        
        # Get vendor analytics for the period
        analytics = VendorAnalytics.objects.filter(
            vendor=vendor,
            date__range=[period_start, period_end]
        )
        
        if not analytics.exists():
            return 50  # Neutral score if no data
        
        avg_response_time = analytics.aggregate(
            avg=Avg('response_time_minutes')
        )['avg'] or 0
        
        avg_response_hours = avg_response_time / 60
        
        # Convert response time to 0-100 score (lower is better)
        if avg_response_hours <= self.thresholds['fast_response_hours']:
            score = 95 + (self.thresholds['fast_response_hours'] - avg_response_hours) * 2.5
        elif avg_response_hours <= self.thresholds['good_response_hours']:
            score = 80 - ((avg_response_hours - self.thresholds['fast_response_hours']) / 4) * 15
        else:
            score = max(0, 80 - (avg_response_hours - self.thresholds['good_response_hours']) * 5)
        
        return min(100, max(0, score))
    
    def _calculate_repeat_customers_score(self, vendor, period_start, period_end):
        """Calculate score based on repeat customer rate"""
        
        # Get all bookings for the vendor
        all_bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            status='completed'
        )
        
        # Get unique customers
        unique_customers = all_bookings.values('user').distinct().count()
        
        if unique_customers == 0:
            return 0
        
        # Find customers with multiple bookings
        repeat_customers = all_bookings.values('user').annotate(
            booking_count=Count('id')
        ).filter(booking_count__gt=1).count()
        
        repeat_rate = (repeat_customers / unique_customers) * 100
        
        # Convert repeat rate to 0-100 score
        if repeat_rate >= self.thresholds['high_repeat_rate']:
            score = 85 + ((repeat_rate - self.thresholds['high_repeat_rate']) / 40) * 15
        elif repeat_rate >= self.thresholds['good_repeat_rate']:
            score = 70 + ((repeat_rate - self.thresholds['good_repeat_rate']) / 20) * 15
        else:
            score = (repeat_rate / self.thresholds['good_repeat_rate']) * 70
        
        return min(100, max(0, score))
    
    def _calculate_performance_trends_score(self, vendor, period_start, period_end):
        """Calculate score based on performance trends over time"""
        
        # Get performance data for current and previous periods
        current_period_days = (period_end - period_start).days
        previous_period_start = period_start - timedelta(days=current_period_days)
        previous_period_end = period_start
        
        current_analytics = VendorAnalytics.objects.filter(
            vendor=vendor,
            date__range=[period_start, period_end]
        ).aggregate(
            avg_rating=Avg('average_rating'),
            total_completed=Sum('bookings_completed'),
            total_received=Sum('bookings_received')
        )
        
        previous_analytics = VendorAnalytics.objects.filter(
            vendor=vendor,
            date__range=[previous_period_start, previous_period_end]
        ).aggregate(
            avg_rating=Avg('average_rating'),
            total_completed=Sum('bookings_completed'),
            total_received=Sum('bookings_received')
        )
        
        # Calculate trends
        trends = []
        
        # Rating trend
        if (current_analytics['avg_rating'] and previous_analytics['avg_rating']):
            rating_change = current_analytics['avg_rating'] - previous_analytics['avg_rating']
            trends.append(rating_change)
        
        # Completion rate trend
        if (current_analytics['total_completed'] and current_analytics['total_received'] and
            previous_analytics['total_completed'] and previous_analytics['total_received']):
            current_completion = current_analytics['total_completed'] / current_analytics['total_received']
            previous_completion = previous_analytics['total_completed'] / previous_analytics['total_received']
            completion_change = current_completion - previous_completion
            trends.append(completion_change * 100)  # Convert to percentage points
        
        if not trends:
            return 50  # Neutral if no trend data
        
        # Calculate average trend
        avg_trend = sum(trends) / len(trends)
        
        # Convert trend to score
        if avg_trend > 0.1:  # Improving
            score = 75 + min(25, avg_trend * 50)
        elif avg_trend < -0.1:  # Declining
            score = 50 + max(-25, avg_trend * 50)
        else:  # Stable
            score = 65
        
        return min(100, max(0, score))
    
    def _get_vendor_metrics(self, vendor, period_start, period_end):
        """Get supporting metrics for quality score calculation"""
        
        bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            created_at__date__range=[period_start, period_end]
        )
        
        total_bookings = bookings.count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Get average rating
        reviews = ServiceReview.objects.filter(
            service__vendor_profile=vendor,
            created_at__date__range=[period_start, period_end]
        )
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Get average response time
        analytics = VendorAnalytics.objects.filter(
            vendor=vendor,
            date__range=[period_start, period_end]
        )
        avg_response_time_minutes = analytics.aggregate(
            avg=Avg('response_time_minutes')
        )['avg'] or 0
        avg_response_time_hours = avg_response_time_minutes / 60
        
        # Calculate repeat customer rate
        all_bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            status='completed'
        )
        unique_customers = all_bookings.values('user').distinct().count()
        repeat_customers = all_bookings.values('user').annotate(
            booking_count=Count('id')
        ).filter(booking_count__gt=1).count()
        
        repeat_customer_rate = 0
        if unique_customers > 0:
            repeat_customer_rate = (repeat_customers / unique_customers) * 100
        
        # Determine trend direction
        trend_direction = 'stable'
        # This could be enhanced with more sophisticated trend analysis
        
        return {
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'avg_rating': round(avg_rating, 2),
            'avg_response_time_hours': round(avg_response_time_hours, 2),
            'repeat_customer_rate': round(repeat_customer_rate, 2),
            'trend_direction': trend_direction,
        }
    
    def calculate_all_vendor_scores(self, period_start=None, period_end=None):
        """Calculate quality scores for all active vendors"""
        
        vendors = VendorProfile.objects.filter(status='active')
        scores = []
        
        for vendor in vendors:
            try:
                score = self.calculate_quality_score(vendor, period_start, period_end)
                scores.append(score)
                logger.info(f"Calculated score for {vendor.business_name}: {score.overall_score}")
            except Exception as e:
                logger.error(f"Error calculating score for {vendor.business_name}: {str(e)}")
        
        return scores
    
    def update_vendor_rankings(self, period_start=None, period_end=None):
        """Update vendor rankings based on quality scores"""
        
        if not period_end:
            period_end = timezone.now().date()
        if not period_start:
            period_start = period_end - timedelta(days=90)
        
        # Get all quality scores for the period
        quality_scores = QualityScore.objects.filter(
            period_start=period_start,
            period_end=period_end
        ).order_by('-overall_score')
        
        # Update overall rankings
        for rank, score in enumerate(quality_scores, 1):
            VendorRanking.objects.update_or_create(
                vendor=score.vendor,
                service_category=None,  # Overall ranking
                ranking_date=timezone.now().date(),
                defaults={
                    'overall_rank': rank,
                    'quality_rank': rank,
                    'performance_rank': rank,
                    'customer_satisfaction_rank': rank,
                    'quality_score': score.overall_score,
                    'performance_score': score.overall_score,
                    'customer_satisfaction_score': score.customer_ratings_score,
                    'total_vendors': quality_scores.count(),
                    'period_start': period_start,
                    'period_end': period_end,
                }
            )
        
        logger.info(f"Updated rankings for {quality_scores.count()} vendors")
    
    def award_certifications(self, vendor, quality_score):
        """Award quality certifications based on performance"""
        
        certifications_to_award = []
        
        # Quality Excellence (90+ overall score)
        if quality_score.overall_score >= 90:
            certifications_to_award.append('quality_excellence')
        
        # Customer Favorite (95+ customer ratings score)
        if quality_score.customer_ratings_score >= 95:
            certifications_to_award.append('customer_favorite')
        
        # Reliable Service (95+ completion rate score)
        if quality_score.completion_rate_score >= 95:
            certifications_to_award.append('reliable_service')
        
        # Fast Response (90+ response time score)
        if quality_score.response_time_score >= 90:
            certifications_to_award.append('fast_response')
        
        # Top Performer (overall rank in top 10%)
        try:
            ranking = VendorRanking.objects.filter(
                vendor=vendor,
                service_category=None
            ).latest('ranking_date')
            
            if ranking.percentile >= 90:
                certifications_to_award.append('top_performer')
        except VendorRanking.DoesNotExist:
            pass
        
        # Award certifications
        for cert_type in certifications_to_award:
            valid_until = timezone.now().date() + timedelta(days=365)  # Valid for 1 year
            
            QualityCertification.objects.get_or_create(
                vendor=vendor,
                certification_type=cert_type,
                awarded_date=timezone.now().date(),
                defaults={
                    'valid_until': valid_until,
                    'min_quality_score': 80,  # Minimum required score
                    'achieved_quality_score': quality_score.overall_score,
                    'criteria_met': {
                        'overall_score': float(quality_score.overall_score),
                        'period': f"{quality_score.period_start} to {quality_score.period_end}",
                    }
                }
            )
        
        logger.info(f"Awarded {len(certifications_to_award)} certifications to {vendor.business_name}")
        
        return certifications_to_award


# Initialize the quality scoring engine
quality_scoring_engine = QualityScoringEngine()