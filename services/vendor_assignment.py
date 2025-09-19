"""
Smart Vendor Assignment System for Hawwa Platform
AI-powered vendor selection based on multiple factors
"""

from django.db.models import Q, Avg, Count, F, Case, When, FloatField
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from datetime import datetime, timedelta
import math
import logging

from .models import Service, ServiceCategory
from vendors.models import VendorProfile, VendorAvailability, VendorBlackoutDate
from bookings.models import Booking

logger = logging.getLogger(__name__)


class VendorAssignmentEngine:
    """
    AI-powered vendor assignment engine that considers multiple factors:
    - Vendor availability and workload
    - Geographic proximity to customer
    - Historical performance ratings
    - Service specialization match
    - Pricing competitiveness
    - Response time history
    - Customer preferences
    """
    
    def __init__(self):
        self.weights = {
            'availability': 0.25,      # 25% - Can vendor handle the booking
            'proximity': 0.20,         # 20% - Geographic distance
            'rating': 0.20,           # 20% - Historical performance
            'specialization': 0.15,    # 15% - Service category expertise
            'pricing': 0.10,          # 10% - Competitive pricing
            'response_time': 0.10,     # 10% - Quick response history
        }
    
    def assign_vendors(self, service_category, customer_location=None, 
                      booking_date=None, booking_time=None, max_vendors=5,
                      customer_preferences=None):
        """
        Main method to find and rank the best vendors for a service request
        
        Args:
            service_category: ServiceCategory or category name
            customer_location: Dict with 'latitude', 'longitude' 
            booking_date: Date object for the service
            booking_time: Time object for the service
            max_vendors: Maximum number of vendors to return
            customer_preferences: Dict with customer preferences
            
        Returns:
            List of tuples: (vendor_profile, score, reasons)
        """
        
        # Get category object if string provided
        if isinstance(service_category, str):
            try:
                service_category = ServiceCategory.objects.get(name=service_category)
            except ServiceCategory.DoesNotExist:
                logger.error(f"Service category '{service_category}' not found")
                return []
        
        # Get vendors who offer services in this category
        vendors = self._get_eligible_vendors(service_category, booking_date, booking_time)
        
        if not vendors:
            return []
        
        # Score each vendor
        scored_vendors = []
        for vendor in vendors:
            score, reasons = self._calculate_vendor_score(
                vendor, service_category, customer_location,
                booking_date, booking_time, customer_preferences
            )
            scored_vendors.append((vendor, score, reasons))
        
        # Sort by score (highest first) and return top vendors
        scored_vendors.sort(key=lambda x: x[1], reverse=True)
        return scored_vendors[:max_vendors]
    
    def _get_eligible_vendors(self, service_category, booking_date=None, booking_time=None):
        """
        Get vendors who are eligible to provide services in the given category
        """
        # Get vendors who have services in this category
        vendor_ids = Service.objects.filter(
            category=service_category,
            status='available'
        ).values_list('vendor_profile_id', flat=True).distinct()
        
        # Filter vendors who have vendor profiles
        vendors = VendorProfile.objects.filter(
            id__in=vendor_ids,
            status='active',
            verified=True
        )
        
        # If date/time specified, filter by availability
        if booking_date and booking_time:
            vendors = self._filter_by_availability(vendors, booking_date, booking_time)
        
        return vendors
    
    def _filter_by_availability(self, vendors, booking_date, booking_time):
        """
        Filter vendors based on their availability for the specified date/time
        """
        available_vendors = []
        
        for vendor in vendors:
            if self._is_vendor_available(vendor, booking_date, booking_time):
                available_vendors.append(vendor)
        
        return available_vendors
    
    def _is_vendor_available(self, vendor, booking_date, booking_time):
        """
        Check if a vendor is available on a specific date and time
        """
        # Check blackout dates
        blackout_conflicts = VendorBlackoutDate.objects.filter(
            vendor=vendor,
            start_date__lte=booking_date,
            end_date__gte=booking_date
        ).exists()
        
        if blackout_conflicts:
            return False
        
        # Check day of week availability
        day_name = booking_date.strftime('%A').lower()
        try:
            availability = VendorAvailability.objects.get(
                vendor=vendor,
                day_of_week=day_name,
                is_available=True
            )
            
            # Check if time falls within available hours
            if availability.start_time <= booking_time <= availability.end_time:
                return True
                
        except VendorAvailability.DoesNotExist:
            # If no specific availability set, assume available
            return True
        
        return False
    
    def _calculate_vendor_score(self, vendor, service_category, customer_location=None,
                               booking_date=None, booking_time=None, customer_preferences=None):
        """
        Calculate comprehensive score for a vendor based on multiple factors
        """
        scores = {}
        reasons = []
        
        # 1. Availability Score (25%)
        availability_score = self._calculate_availability_score(vendor, booking_date, booking_time)
        scores['availability'] = availability_score
        if availability_score > 0.8:
            reasons.append("High availability")
        
        # 2. Proximity Score (20%)
        proximity_score = self._calculate_proximity_score(vendor, customer_location)
        scores['proximity'] = proximity_score
        if proximity_score > 0.8:
            reasons.append("Close to your location")
        
        # 3. Rating Score (20%)
        rating_score = self._calculate_rating_score(vendor)
        scores['rating'] = rating_score
        if rating_score > 0.8:
            reasons.append("Highly rated")
        
        # 4. Specialization Score (15%)
        specialization_score = self._calculate_specialization_score(vendor, service_category)
        scores['specialization'] = specialization_score
        if specialization_score > 0.8:
            reasons.append("Specialized in this service")
        
        # 5. Pricing Score (10%)
        pricing_score = self._calculate_pricing_score(vendor, service_category)
        scores['pricing'] = pricing_score
        if pricing_score > 0.8:
            reasons.append("Competitive pricing")
        
        # 6. Response Time Score (10%)
        response_score = self._calculate_response_time_score(vendor)
        scores['response_time'] = response_score
        if response_score > 0.8:
            reasons.append("Quick response time")
        
        # Calculate weighted total score
        total_score = sum(scores[factor] * self.weights[factor] for factor in scores)
        
        return total_score, reasons
    
    def _calculate_availability_score(self, vendor, booking_date=None, booking_time=None):
        """
        Calculate availability score based on workload and schedule
        """
        if not booking_date:
            return 1.0  # Perfect score if no specific date required
        
        # Check current workload for the date
        existing_bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            start_date=booking_date,
            status__in=['confirmed', 'in_progress']
        ).count()
        
        # Assume max 5 bookings per day for now
        max_daily_bookings = 5
        workload_ratio = existing_bookings / max_daily_bookings
        
        # Higher workload = lower availability score
        workload_score = max(0, 1 - workload_ratio)
        
        # If specific time given, check for conflicts
        time_conflict_penalty = 0
        if booking_time:
            # Check for overlapping bookings (simplified - assuming 2-hour buffer)
            buffer_hours = 2
            start_buffer = (datetime.combine(booking_date, booking_time) - 
                          timedelta(hours=buffer_hours)).time()
            end_buffer = (datetime.combine(booking_date, booking_time) + 
                        timedelta(hours=buffer_hours)).time()
            
            conflicts = Booking.objects.filter(
                service__vendor_profile=vendor,
                start_date=booking_date,
                start_time__gte=start_buffer,
                start_time__lte=end_buffer,
                status__in=['confirmed', 'in_progress']
            ).count()
            
            time_conflict_penalty = min(0.5, conflicts * 0.2)
        
        final_score = max(0, workload_score - time_conflict_penalty)
        return final_score
    
    def _calculate_proximity_score(self, vendor, customer_location):
        """
        Calculate proximity score based on geographic distance
        """
        if not customer_location:
            return 0.5  # Neutral score if location not provided
        
        # For now, use service areas text matching
        # In production, would use actual GPS coordinates
        service_areas = vendor.service_areas.lower()
        
        # Simple keyword matching - in production would use proper geocoding
        location_keywords = ['doha', 'qatar', 'west bay', 'pearl', 'lusail']
        
        # If vendor serves the general area, give good score
        for keyword in location_keywords:
            if keyword in service_areas:
                return 0.8
        
        # Default to moderate score
        return 0.6
    
    def _calculate_rating_score(self, vendor):
        """
        Calculate score based on vendor's historical ratings
        """
        if vendor.total_reviews == 0:
            return 0.5  # Neutral score for new vendors
        
        # Normalize rating (1-5 scale to 0-1 scale)
        rating_score = (vendor.average_rating - 1) / 4
        
        # Apply confidence factor based on number of reviews
        confidence_factor = min(1.0, vendor.total_reviews / 20)  # Full confidence at 20+ reviews
        
        return rating_score * confidence_factor + 0.5 * (1 - confidence_factor)
    
    def _calculate_specialization_score(self, vendor, service_category):
        """
        Calculate score based on vendor's expertise in the service category
        """
        # Count services vendor offers in this category
        category_services = Service.objects.filter(
            vendor_profile=vendor,
            category=service_category,
            status='available'
        ).count()
        
        # Count total services vendor offers
        total_services = Service.objects.filter(
            vendor_profile=vendor,
            status='available'
        ).count()
        
        if total_services == 0:
            return 0.3  # Low score if no active services
        
        # Higher ratio = more specialized
        specialization_ratio = category_services / total_services
        
        # Bonus for having multiple services in category
        category_bonus = min(0.3, category_services * 0.1)
        
        return min(1.0, specialization_ratio + category_bonus)
    
    def _calculate_pricing_score(self, vendor, service_category):
        """
        Calculate score based on competitive pricing
        """
        # Get vendor's average price for services in this category
        vendor_services = Service.objects.filter(
            vendor_profile=vendor,
            category=service_category,
            status='available'
        )
        
        if not vendor_services.exists():
            return 0.5  # Neutral if no services
        
        vendor_avg_price = vendor_services.aggregate(
            avg_price=Avg('price')
        )['avg_price']
        
        # Get market average for this category
        market_avg_price = Service.objects.filter(
            category=service_category,
            status='available'
        ).aggregate(avg_price=Avg('price'))['avg_price']
        
        if not market_avg_price or market_avg_price == 0:
            return 0.5
        
        # Score based on how competitive the pricing is
        price_ratio = vendor_avg_price / market_avg_price
        
        # Best score for prices 10-20% below market average
        if 0.8 <= price_ratio <= 0.9:
            return 1.0
        elif 0.9 < price_ratio <= 1.0:
            return 0.8
        elif 1.0 < price_ratio <= 1.1:
            return 0.6
        elif 1.1 < price_ratio <= 1.2:
            return 0.4
        else:
            return 0.2  # Very expensive or very cheap (suspicious)
    
    def _calculate_response_time_score(self, vendor):
        """
        Calculate score based on vendor's response time history
        """
        # Get vendor's booking acceptance/response patterns
        recent_bookings = Booking.objects.filter(
            service__vendor_profile=vendor,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:20]  # Last 20 bookings
        
        if not recent_bookings:
            return 0.5  # Neutral for new vendors
        
        # For now, use a simplified calculation
        # In production, would track actual response times
        
        # Use completion rate as proxy for responsiveness
        completion_rate = vendor.get_completion_rate() / 100
        
        # Recent activity bonus
        recent_activity = min(1.0, recent_bookings.count() / 10)
        
        return (completion_rate * 0.7) + (recent_activity * 0.3)
    
    def get_vendor_assignment_explanation(self, vendor, score, reasons):
        """
        Generate human-readable explanation for vendor assignment
        """
        explanation = f"Vendor {vendor.business_name} scored {score:.2f} (out of 1.0)\n"
        explanation += f"Match score: {int(score * 100)}%\n\n"
        explanation += "Reasons for recommendation:\n"
        
        for reason in reasons:
            explanation += f"• {reason}\n"
        
        explanation += f"\nVendor details:\n"
        explanation += f"• Average rating: {vendor.average_rating}/5 ({vendor.total_reviews} reviews)\n"
        explanation += f"• Completion rate: {vendor.get_completion_rate():.1f}%\n"
        explanation += f"• Service areas: {vendor.service_areas}\n"
        
        return explanation


class VendorRecommendationAPI:
    """
    API wrapper for vendor assignment system
    """
    
    def __init__(self):
        self.engine = VendorAssignmentEngine()
    
    def recommend_vendors_for_booking(self, service_category, customer_user=None,
                                    customer_location=None, booking_date=None, 
                                    booking_time=None, max_recommendations=5):
        """
        Get vendor recommendations for a new booking
        """
        customer_preferences = None
        if customer_user:
            customer_preferences = self._get_customer_preferences(customer_user)
        
        recommendations = self.engine.assign_vendors(
            service_category=service_category,
            customer_location=customer_location,
            booking_date=booking_date,
            booking_time=booking_time,
            max_vendors=max_recommendations,
            customer_preferences=customer_preferences
        )
        
        return [
            {
                'vendor': vendor,
                'match_score': int(score * 100),
                'reasons': reasons,
                'explanation': self.engine.get_vendor_assignment_explanation(vendor, score, reasons)
            }
            for vendor, score, reasons in recommendations
        ]
    
    def _get_customer_preferences(self, customer_user):
        """
        Extract customer preferences from their booking history
        """
        # Analyze past bookings to understand preferences
        past_bookings = Booking.objects.filter(
            user=customer_user,
            status='completed'
        ).select_related('service__vendor_profile')
        
        preferences = {
            'preferred_vendors': [],
            'preferred_price_range': None,
            'preferred_service_types': [],
        }
        
        if past_bookings.exists():
            # Extract preferred vendors (those used multiple times)
            vendor_counts = {}
            for booking in past_bookings:
                vendor = booking.service.vendor_profile
                vendor_counts[vendor.id] = vendor_counts.get(vendor.id, 0) + 1
            
            # Vendors used more than once are preferred
            preferences['preferred_vendors'] = [
                vendor_id for vendor_id, count in vendor_counts.items() if count > 1
            ]
        
        return preferences
    
    def auto_assign_vendor(self, booking_request):
        """
        Automatically assign the best vendor to a booking request
        """
        recommendations = self.recommend_vendors_for_booking(
            service_category=booking_request.get('service_category'),
            customer_user=booking_request.get('customer'),
            customer_location=booking_request.get('location'),
            booking_date=booking_request.get('date'),
            booking_time=booking_request.get('time'),
            max_recommendations=1
        )
        
        if recommendations:
            return recommendations[0]['vendor']
        
        return None


# Global instance for easy access
vendor_assignment_engine = VendorRecommendationAPI()