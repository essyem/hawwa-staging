"""
Smart Vendor Assignment Service

This service implements AI-powered vendor assignment using multiple factors:
- Quality scores from analytics
- Location proximity
- Vendor availability
- Current workload
- Customer preferences
- Historical performance
"""

import logging
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, F, Avg, Count, Case, When, Value
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.gis.measure import D
from geopy.distance import geodesic
import math

# Import models
from vendors.models import VendorProfile
from bookings.models import Booking
from services.models import Service, ServiceCategory
from analytics.models import QualityScore, PerformanceMetrics
from .assignment_models import (
    VendorAssignment, VendorAvailability, VendorWorkload, 
    AssignmentPreference, AssignmentLog
)

logger = logging.getLogger(__name__)


class SmartVendorAssignmentEngine:
    """
    AI-powered vendor assignment engine that considers multiple factors
    to find the best vendor match for each booking request.
    """
    
    def __init__(self):
        # Assignment weights (must sum to 1.0)
        self.weights = {
            'quality_score': 0.35,      # 35% - Vendor quality and performance
            'location_proximity': 0.25,  # 25% - Distance and travel time
            'availability': 0.20,       # 20% - Vendor availability
            'workload': 0.15,          # 15% - Current workload balance
            'customer_preference': 0.05 # 5% - Customer/vendor preferences
        }
        
        # Scoring thresholds
        self.quality_thresholds = {
            'excellent': 90,
            'good': 80,
            'average': 70,
            'minimum': 60
        }
        
        # Distance thresholds (in km)
        self.distance_thresholds = {
            'very_close': 5,
            'close': 15,
            'moderate': 30,
            'far': 50,
            'very_far': 100
        }
        
        # Response time requirements (in minutes)
        self.response_time_requirements = {
            'urgent': 15,
            'high': 30,
            'normal': 60,
            'low': 120
        }
    
    def find_best_vendors(self, booking: Booking, max_vendors: int = 5) -> List[Dict]:
        """
        Find the best vendor matches for a booking using AI scoring.
        
        Args:
            booking: The booking to assign
            max_vendors: Maximum number of vendors to return
            
        Returns:
            List of vendor assignment recommendations with scores
        """
        try:
            logger.info(f"Finding best vendors for booking {booking.booking_number}")
            
            # Step 1: Get eligible vendors
            eligible_vendors = self._get_eligible_vendors(booking)
            
            if not eligible_vendors:
                logger.warning(f"No eligible vendors found for booking {booking.booking_number}")
                return []
            
            # Step 2: Calculate comprehensive scores for each vendor
            vendor_scores = []
            for vendor in eligible_vendors:
                score_data = self._calculate_vendor_score(booking, vendor)
                if score_data['total_score'] > 0:
                    vendor_scores.append(score_data)
            
            # Step 3: Sort by total score and return top matches
            vendor_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            top_vendors = vendor_scores[:max_vendors]
            
            logger.info(f"Found {len(top_vendors)} vendor recommendations for booking {booking.booking_number}")
            
            return top_vendors
            
        except Exception as e:
            logger.error(f"Error finding vendors for booking {booking.booking_number}: {str(e)}")
            return []
    
    def auto_assign_vendor(self, booking: Booking, confidence_threshold: float = 0.8) -> Optional[VendorAssignment]:
        """
        Automatically assign the best vendor if confidence is high enough.
        
        Args:
            booking: The booking to assign
            confidence_threshold: Minimum confidence level for auto-assignment
            
        Returns:
            VendorAssignment if successful, None otherwise
        """
        try:
            # Find best vendors
            vendor_recommendations = self.find_best_vendors(booking, max_vendors=1)
            
            if not vendor_recommendations:
                logger.warning(f"No vendor recommendations for auto-assignment of booking {booking.booking_number}")
                return None
            
            best_vendor_data = vendor_recommendations[0]
            
            # Check confidence level
            if best_vendor_data['confidence_level'] < confidence_threshold:
                logger.info(f"Confidence level {best_vendor_data['confidence_level']} below threshold {confidence_threshold} for booking {booking.booking_number}")
                return None
            
            # Create assignment
            assignment = self._create_assignment(booking, best_vendor_data, auto_assign=True)
            
            logger.info(f"Auto-assigned booking {booking.booking_number} to vendor {assignment.vendor.business_name}")
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error in auto-assignment for booking {booking.booking_number}: {str(e)}")
            return None
    
    def create_manual_assignment(self, booking: Booking, vendor: VendorProfile, user=None) -> VendorAssignment:
        """
        Create a manual vendor assignment.
        
        Args:
            booking: The booking to assign
            vendor: The vendor to assign
            user: User creating the assignment
            
        Returns:
            VendorAssignment instance
        """
        try:
            # Calculate scores for the manually selected vendor
            score_data = self._calculate_vendor_score(booking, vendor)
            score_data['assignment_method'] = 'manual'
            score_data['confidence_level'] = Decimal('1.00')  # Manual assignments have 100% confidence
            
            # Create assignment
            assignment = self._create_assignment(booking, score_data, auto_assign=False)
            
            # Log manual assignment
            self._log_assignment_activity(
                assignment, 
                'manual_override', 
                f"Manual assignment by {user.username if user else 'system'}"
            )
            
            logger.info(f"Created manual assignment of booking {booking.booking_number} to vendor {vendor.business_name}")
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error creating manual assignment: {str(e)}")
            raise
    
    def _get_eligible_vendors(self, booking: Booking) -> List[VendorProfile]:
        """
        Get vendors eligible for a specific booking based on basic criteria.
        """
        # Base query for active vendors
        vendors = VendorProfile.objects.filter(
            status='active',
            verified=True
        )
        
        # Filter by service category if specified
        if booking.service and booking.service.category:
            # This would need to be implemented based on how vendors are linked to service categories
            # For now, we'll include all active vendors
            pass
        
        # Filter by location (basic implementation)
        if hasattr(booking, 'city') and booking.city:
            vendors = vendors.filter(
                Q(service_areas__icontains=booking.city) |
                Q(city=booking.city)
            )
        
        # Filter out vendors with quality scores below minimum threshold
        min_quality = self.quality_thresholds['minimum']
        recent_scores = QualityScore.objects.filter(
            vendor__in=vendors,
            calculated_at__gte=timezone.now() - timedelta(days=30)
        ).values('vendor').annotate(
            latest_score=Avg('overall_score')
        ).filter(latest_score__gte=min_quality)
        
        vendor_ids_with_good_scores = [score['vendor'] for score in recent_scores]
        vendors = vendors.filter(id__in=vendor_ids_with_good_scores)
        
        return list(vendors)
    
    def _calculate_vendor_score(self, booking: Booking, vendor: VendorProfile) -> Dict:
        """
        Calculate comprehensive score for a vendor-booking match.
        """
        scores = {
            'vendor': vendor,
            'booking': booking,
            'quality_score': 0,
            'location_score': 0,
            'availability_score': 0,
            'workload_score': 0,
            'preference_score': 0,
            'total_score': 0,
            'confidence_level': 0,
            'distance_km': None,
            'estimated_travel_time': None,
            'assignment_reasoning': {}
        }
        
        # Calculate individual scores
        scores.update(self._calculate_quality_score(vendor))
        scores.update(self._calculate_location_score(booking, vendor))
        scores.update(self._calculate_availability_score(booking, vendor))
        scores.update(self._calculate_workload_score(vendor))
        scores.update(self._calculate_preference_score(booking, vendor))
        
        # Calculate weighted total score
        total_score = (
            scores['quality_score'] * self.weights['quality_score'] +
            scores['location_score'] * self.weights['location_proximity'] +
            scores['availability_score'] * self.weights['availability'] +
            scores['workload_score'] * self.weights['workload'] +
            scores['preference_score'] * self.weights['customer_preference']
        )
        
        scores['total_score'] = round(total_score, 2)
        
        # Calculate confidence level based on data completeness and score distribution
        scores['confidence_level'] = self._calculate_confidence_level(scores)
        
        return scores
    
    def _calculate_quality_score(self, vendor: VendorProfile) -> Dict:
        """Calculate quality-based score for vendor."""
        try:
            # Get recent quality score
            recent_score = QualityScore.objects.filter(
                vendor=vendor,
                calculated_at__gte=timezone.now() - timedelta(days=30)
            ).order_by('-calculated_at').first()
            
            if recent_score:
                quality_score = float(recent_score.overall_score)
                reasoning = {
                    'quality_score_value': quality_score,
                    'score_date': recent_score.calculated_at.isoformat(),
                    'grade': recent_score.grade
                }
            else:
                # Fallback to vendor average rating
                quality_score = float(vendor.average_rating * 20)  # Convert 5-star to 100-point scale
                reasoning = {
                    'quality_score_value': quality_score,
                    'source': 'average_rating',
                    'note': 'No recent quality score available'
                }
            
            return {
                'quality_score': quality_score,
                'assignment_reasoning': {'quality': reasoning}
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality score for vendor {vendor.id}: {str(e)}")
            return {
                'quality_score': 0,
                'assignment_reasoning': {'quality': {'error': str(e)}}
            }
    
    def _calculate_location_score(self, booking: Booking, vendor: VendorProfile) -> Dict:
        """Calculate location-based score considering distance and travel time."""
        try:
            # For now, use a simple distance calculation
            # In production, you'd use actual GPS coordinates and routing APIs
            
            # Mock distance calculation based on city matching
            if hasattr(booking, 'city') and hasattr(vendor, 'city'):
                if booking.city.lower() == vendor.city.lower():
                    distance_km = 5  # Same city
                    location_score = 100
                else:
                    distance_km = 25  # Different city
                    location_score = 60
            else:
                distance_km = 15  # Default moderate distance
                location_score = 75
            
            # Apply distance-based scoring
            if distance_km <= self.distance_thresholds['very_close']:
                location_score = 100
            elif distance_km <= self.distance_thresholds['close']:
                location_score = 85
            elif distance_km <= self.distance_thresholds['moderate']:
                location_score = 70
            elif distance_km <= self.distance_thresholds['far']:
                location_score = 50
            else:
                location_score = 25
            
            # Estimate travel time (rough calculation)
            estimated_travel_time = max(15, distance_km * 2)  # 2 minutes per km, minimum 15 min
            
            reasoning = {
                'distance_km': distance_km,
                'estimated_travel_time_minutes': estimated_travel_time,
                'location_score': location_score
            }
            
            return {
                'location_score': location_score,
                'distance_km': distance_km,
                'estimated_travel_time': estimated_travel_time,
                'assignment_reasoning': {'location': reasoning}
            }
            
        except Exception as e:
            logger.error(f"Error calculating location score: {str(e)}")
            return {
                'location_score': 0,
                'distance_km': None,
                'estimated_travel_time': None,
                'assignment_reasoning': {'location': {'error': str(e)}}
            }
    
    def _calculate_availability_score(self, booking: Booking, vendor: VendorProfile) -> Dict:
        """Calculate availability-based score for the booking time slot."""
        try:
            booking_date = booking.start_date
            booking_start_time = booking.start_time
            
            # Check vendor availability for the booking date
            availability = VendorAvailability.objects.filter(
                vendor=vendor,
                date=booking_date,
                start_time__lte=booking_start_time,
                end_time__gte=booking_start_time
            ).first()
            
            if availability:
                if availability.is_available:
                    availability_score = 100 - availability.capacity_percentage
                    reasoning = {
                        'availability_found': True,
                        'capacity_percentage': availability.capacity_percentage,
                        'current_bookings': availability.current_bookings,
                        'max_bookings': availability.max_concurrent_bookings
                    }
                else:
                    availability_score = 0
                    reasoning = {
                        'availability_found': True,
                        'status': availability.status,
                        'reason': 'Vendor not available at requested time'
                    }
            else:
                # No specific availability record, assume available with moderate score
                availability_score = 75
                reasoning = {
                    'availability_found': False,
                    'assumption': 'No availability record, assuming available'
                }
            
            return {
                'availability_score': availability_score,
                'assignment_reasoning': {'availability': reasoning}
            }
            
        except Exception as e:
            logger.error(f"Error calculating availability score: {str(e)}")
            return {
                'availability_score': 0,
                'assignment_reasoning': {'availability': {'error': str(e)}}
            }
    
    def _calculate_workload_score(self, vendor: VendorProfile) -> Dict:
        """Calculate workload-based score considering current load."""
        try:
            workload, created = VendorWorkload.objects.get_or_create(vendor=vendor)
            
            if created:
                # New workload record, assume light load
                workload_score = 100
                reasoning = {
                    'workload_status': 'new',
                    'active_bookings': 0,
                    'pending_bookings': 0
                }
            else:
                workload_score = workload.workload_score
                reasoning = {
                    'workload_status': workload.workload_status,
                    'active_bookings': workload.active_bookings,
                    'pending_bookings': workload.pending_bookings,
                    'daily_limit': workload.daily_booking_limit,
                    'workload_score': workload_score
                }
            
            return {
                'workload_score': workload_score,
                'assignment_reasoning': {'workload': reasoning}
            }
            
        except Exception as e:
            logger.error(f"Error calculating workload score: {str(e)}")
            return {
                'workload_score': 0,
                'assignment_reasoning': {'workload': {'error': str(e)}}
            }
    
    def _calculate_preference_score(self, booking: Booking, vendor: VendorProfile) -> Dict:
        """Calculate preference-based score from customer and vendor preferences."""
        try:
            preference_score = 50  # Base neutral score
            reasoning = {'base_score': 50}
            
            # Check customer preferences
            if hasattr(booking, 'user'):
                customer_prefs = AssignmentPreference.objects.filter(
                    customer=booking.user,
                    preference_type='customer',
                    is_active=True
                ).first()
                
                if customer_prefs:
                    if vendor in customer_prefs.preferred_vendors.all():
                        preference_score += 30
                        reasoning['customer_preferred'] = True
                    elif vendor in customer_prefs.excluded_vendors.all():
                        preference_score = 0
                        reasoning['customer_excluded'] = True
                    
                    # Check minimum rating requirement
                    if vendor.average_rating < customer_prefs.min_vendor_rating:
                        preference_score = max(0, preference_score - 20)
                        reasoning['rating_below_minimum'] = True
            
            # Check vendor preferences (if they have any restrictions)
            vendor_prefs = AssignmentPreference.objects.filter(
                vendor=vendor,
                preference_type='vendor',
                is_active=True
            ).first()
            
            if vendor_prefs:
                reasoning['vendor_preferences_found'] = True
                # Add vendor preference logic here if needed
            
            return {
                'preference_score': max(0, min(100, preference_score)),
                'assignment_reasoning': {'preferences': reasoning}
            }
            
        except Exception as e:
            logger.error(f"Error calculating preference score: {str(e)}")
            return {
                'preference_score': 50,
                'assignment_reasoning': {'preferences': {'error': str(e)}}
            }
    
    def _calculate_confidence_level(self, scores: Dict) -> Decimal:
        """Calculate confidence level based on data completeness and score consistency."""
        try:
            confidence_factors = []
            
            # Data completeness factor
            data_completeness = 0
            if scores['quality_score'] > 0:
                data_completeness += 0.3
            if scores['location_score'] > 0:
                data_completeness += 0.25
            if scores['availability_score'] > 0:
                data_completeness += 0.2
            if scores['workload_score'] > 0:
                data_completeness += 0.15
            if scores['preference_score'] > 0:
                data_completeness += 0.1
            
            confidence_factors.append(data_completeness)
            
            # Score consistency factor (penalize extreme variations)
            individual_scores = [
                scores['quality_score'], scores['location_score'], 
                scores['availability_score'], scores['workload_score'], 
                scores['preference_score']
            ]
            valid_scores = [s for s in individual_scores if s > 0]
            
            if valid_scores:
                score_variance = Decimal(str(self._calculate_variance(valid_scores)))
                consistency_factor = max(0, 1 - (score_variance / 1000))
                confidence_factors.append(float(consistency_factor))
            
            # Overall score factor (higher scores get higher confidence)
            score_factor = scores['total_score'] / 100
            confidence_factors.append(score_factor)
            
            # Calculate weighted average
            confidence = sum(confidence_factors) / len(confidence_factors)
            
            return Decimal(str(round(confidence, 2)))
            
        except Exception as e:
            logger.error(f"Error calculating confidence level: {str(e)}")
            return Decimal('0.50')
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores for consistency measurement."""
        if len(scores) < 2:
            return 0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance
    
    def _create_assignment(self, booking: Booking, vendor_data: Dict, auto_assign: bool = False) -> VendorAssignment:
        """Create a VendorAssignment record from scoring data."""
        try:
            assignment = VendorAssignment.objects.create(
                booking=booking,
                vendor=vendor_data['vendor'],
                status='auto_assigned' if auto_assign else 'pending',
                assignment_method='smart_ai' if auto_assign else 'manual',
                total_score=Decimal(str(vendor_data['total_score'])),
                quality_score=Decimal(str(vendor_data['quality_score'])),
                location_score=Decimal(str(vendor_data['location_score'])),
                availability_score=Decimal(str(vendor_data['availability_score'])),
                workload_score=Decimal(str(vendor_data['workload_score'])),
                preference_score=Decimal(str(vendor_data['preference_score'])),
                distance_km=Decimal(str(vendor_data['distance_km'])) if vendor_data['distance_km'] else None,
                estimated_travel_time_minutes=vendor_data['estimated_travel_time'],
                assignment_reasoning=vendor_data['assignment_reasoning'],
                confidence_level=vendor_data['confidence_level']
            )
            
            # Log assignment creation
            self._log_assignment_activity(
                assignment,
                'assignment_created',
                f"{'Auto-assigned' if auto_assign else 'Created'} with score {vendor_data['total_score']}"
            )
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error creating assignment: {str(e)}")
            raise
    
    def _log_assignment_activity(self, assignment: VendorAssignment, log_type: str, message: str, details: Dict = None):
        """Log assignment activity for audit and analytics."""
        try:
            AssignmentLog.objects.create(
                assignment=assignment,
                log_type=log_type,
                message=message,
                details=details or {}
            )
        except Exception as e:
            logger.error(f"Error logging assignment activity: {str(e)}")


# Global instance
smart_assignment_engine = SmartVendorAssignmentEngine()