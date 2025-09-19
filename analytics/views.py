"""
Views for Performance Analytics Dashboard
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import (
    QualityScore, PerformanceMetrics, VendorRanking, QualityCertification,
    VendorAvailability, VendorWorkload, VendorAssignment, AssignmentPreference,
    AssignmentLog
)
from vendors.models import VendorProfile
from bookings.models import Booking
from services.models import ServiceReview, ServiceCategory
from .services import QualityScoringEngine
from .assignment_service import smart_assignment_engine


@staff_member_required
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    
    # Date range (last 30 days by default)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Platform statistics
    platform_stats = _get_platform_statistics(start_date, end_date)
    
    # Top performers
    top_vendors = _get_top_performers(start_date, end_date, limit=5)
    
    # Recent alerts
    recent_alerts = _get_recent_quality_alerts(limit=10)
    
    # Chart data
    chart_data = _get_dashboard_chart_data(start_date, end_date)
    
    context = {
        'platform_stats': platform_stats,
        'top_vendors': top_vendors,
        'recent_alerts': recent_alerts,
        'chart_data': chart_data,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/dashboard.html', context)


@staff_member_required
def vendor_analytics_detail(request, vendor_id):
    """Detailed analytics view for a specific vendor"""
    
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # 3 months
    
    # Quality scores history
    quality_scores = QualityScore.objects.filter(
        vendor=vendor,
        period_start__gte=start_date
    ).order_by('-calculated_at')
    
    # Performance metrics
    performance_metrics = PerformanceMetrics.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Rankings
    rankings = VendorRanking.objects.filter(
        vendor=vendor,
        period_start__gte=start_date
    ).order_by('-ranking_date')
    
    # Certifications
    certifications = QualityCertification.objects.filter(
        vendor=vendor,
        is_active=True
    ).order_by('-awarded_date')
    
    # Aggregated metrics
    aggregated_metrics = _get_vendor_aggregated_metrics(vendor, start_date, end_date)
    
    # Chart data for this vendor
    vendor_chart_data = _get_vendor_chart_data(vendor, start_date, end_date)
    
    context = {
        'vendor': vendor,
        'quality_scores': quality_scores[:10],
        'performance_metrics': performance_metrics[:30],
        'rankings': rankings[:5],
        'certifications': certifications,
        'aggregated_metrics': aggregated_metrics,
        'chart_data': vendor_chart_data,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/vendor_detail.html', context)


@staff_member_required
def quality_rankings(request):
    """Quality rankings view"""
    
    # Get latest rankings
    latest_rankings = VendorRanking.objects.filter(
        service_category__isnull=True  # Overall rankings
    ).order_by('overall_rank')[:50]
    
    # Category-specific rankings
    categories = ServiceCategory.objects.all()
    category_rankings = {}
    
    for category in categories:
        category_rankings[category.name] = VendorRanking.objects.filter(
            service_category=category
        ).order_by('overall_rank')[:10]
    
    context = {
        'overall_rankings': latest_rankings,
        'category_rankings': category_rankings,
        'categories': categories,
    }
    
    return render(request, 'analytics/rankings.html', context)


@staff_member_required
def performance_trends(request):
    """Performance trends view"""
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)
    
    # Platform trends
    platform_trends = _get_platform_trends(start_date, end_date)
    
    # Vendor performance distribution
    vendor_distribution = _get_vendor_performance_distribution()
    
    # Category performance
    category_performance = _get_category_performance(start_date, end_date)
    
    context = {
        'platform_trends': platform_trends,
        'vendor_distribution': vendor_distribution,
        'category_performance': category_performance,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/trends.html', context)


@login_required
def vendor_dashboard(request):
    """Dashboard view for individual vendors"""
    
    # Check if user has vendor profile
    try:
        vendor = request.user.vendor_profile
    except:
        return render(request, 'analytics/no_vendor_profile.html')
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Latest quality score
    latest_score = QualityScore.objects.filter(
        vendor=vendor
    ).order_by('-calculated_at').first()
    
    # Recent performance metrics
    recent_metrics = PerformanceMetrics.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Rankings
    latest_ranking = VendorRanking.objects.filter(
        vendor=vendor,
        service_category__isnull=True
    ).order_by('-ranking_date').first()
    
    # Active certifications
    certifications = QualityCertification.objects.filter(
        vendor=vendor,
        is_active=True
    )
    
    # Performance summary
    performance_summary = _get_vendor_performance_summary(vendor, start_date, end_date)
    
    context = {
        'vendor': vendor,
        'latest_score': latest_score,
        'recent_metrics': recent_metrics[:7],  # Last 7 days
        'latest_ranking': latest_ranking,
        'certifications': certifications,
        'performance_summary': performance_summary,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/vendor_dashboard.html', context)


# API endpoints for chart data
@staff_member_required
def api_platform_stats(request):
    """API endpoint for platform statistics"""
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    stats = _get_platform_statistics(start_date, end_date)
    
    return JsonResponse(stats)


@staff_member_required
def api_vendor_performance_chart(request, vendor_id):
    """API endpoint for vendor performance chart data"""
    
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    chart_data = _get_vendor_chart_data(vendor, start_date, end_date)
    
    return JsonResponse(chart_data)


@staff_member_required
def api_quality_trends(request):
    """API endpoint for quality trends data"""
    
    days = int(request.GET.get('days', 90))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    trends = _get_platform_trends(start_date, end_date)
    
    return JsonResponse(trends)


# Helper functions
def _get_platform_statistics(start_date, end_date):
    """Get platform-wide statistics"""
    
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
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    avg_rating = ServiceReview.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    avg_quality_score = QualityScore.objects.filter(
        period_start__gte=start_date,
        period_end__lte=end_date
    ).aggregate(avg=Avg('overall_score'))['avg'] or 0
    
    # Growth metrics
    prev_start = start_date - timedelta(days=(end_date - start_date).days)
    prev_bookings = Booking.objects.filter(
        created_at__date__range=[prev_start, start_date]
    ).count()
    
    booking_growth = ((total_bookings - prev_bookings) / prev_bookings * 100) if prev_bookings > 0 else 0
    
    return {
        'total_vendors': total_vendors,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'completion_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
        'total_revenue': float(total_revenue),
        'avg_rating': round(float(avg_rating), 2),
        'avg_quality_score': round(float(avg_quality_score), 1),
        'booking_growth': round(booking_growth, 1),
    }


def _get_top_performers(start_date, end_date, limit=5):
    """Get top performing vendors"""
    
    top_scores = QualityScore.objects.filter(
        period_start__gte=start_date,
        period_end__lte=end_date
    ).order_by('-overall_score')[:limit]
    
    return top_scores


def _get_recent_quality_alerts(limit=10):
    """Get recent quality alerts (simplified)"""
    
    # This would connect to a real alerting system
    # For now, return vendors with low scores
    low_scores = QualityScore.objects.filter(
        overall_score__lt=70,
        calculated_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-calculated_at')[:limit]
    
    alerts = []
    for score in low_scores:
        alerts.append({
            'vendor': score.vendor,
            'message': f"Quality score {score.overall_score:.1f}/100 below threshold",
            'severity': 'high' if score.overall_score < 60 else 'medium',
            'timestamp': score.calculated_at,
        })
    
    return alerts


def _get_dashboard_chart_data(start_date, end_date):
    """Get chart data for dashboard"""
    
    # Daily booking trends
    daily_bookings = []
    current_date = start_date
    
    while current_date <= end_date:
        bookings_count = Booking.objects.filter(
            created_at__date=current_date
        ).count()
        
        daily_bookings.append({
            'date': current_date.isoformat(),
            'bookings': bookings_count,
        })
        
        current_date += timedelta(days=1)
    
    # Quality score distribution
    score_ranges = [
        (90, 100, 'Excellent'),
        (80, 89, 'Good'),
        (70, 79, 'Average'),
        (60, 69, 'Below Average'),
        (0, 59, 'Poor'),
    ]
    
    score_distribution = []
    for min_score, max_score, label in score_ranges:
        count = QualityScore.objects.filter(
            overall_score__gte=min_score,
            overall_score__lte=max_score,
            calculated_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        score_distribution.append({
            'label': label,
            'count': count,
            'range': f"{min_score}-{max_score}",
        })
    
    return {
        'daily_bookings': daily_bookings,
        'score_distribution': score_distribution,
    }


def _get_vendor_aggregated_metrics(vendor, start_date, end_date):
    """Get aggregated metrics for a vendor"""
    
    metrics = PerformanceMetrics.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    )
    
    if not metrics.exists():
        return {
            'total_bookings': 0,
            'completion_rate': 0,
            'avg_rating': 0,
            'total_revenue': 0,
            'repeat_customer_rate': 0,
        }
    
    total_received = metrics.aggregate(Sum('bookings_received'))['bookings_received__sum'] or 0
    total_completed = metrics.aggregate(Sum('bookings_completed'))['bookings_completed__sum'] or 0
    total_revenue = metrics.aggregate(Sum('revenue'))['revenue__sum'] or Decimal('0.00')
    
    # Weighted average rating
    total_ratings = metrics.aggregate(Sum('total_ratings'))['total_ratings__sum'] or 0
    if total_ratings > 0:
        weighted_rating_sum = sum(
            metric.avg_rating * metric.total_ratings 
            for metric in metrics 
            if metric.total_ratings > 0
        )
        avg_rating = weighted_rating_sum / total_ratings
    else:
        avg_rating = 0
    
    # Repeat customer rate
    total_customers = metrics.aggregate(Sum('total_unique_customers'))['total_unique_customers__sum'] or 0
    total_repeat = metrics.aggregate(Sum('repeat_customers'))['repeat_customers__sum'] or 0
    repeat_rate = (total_repeat / total_customers * 100) if total_customers > 0 else 0
    
    return {
        'total_bookings': total_received,
        'completion_rate': (total_completed / total_received * 100) if total_received > 0 else 0,
        'avg_rating': round(avg_rating, 2),
        'total_revenue': float(total_revenue),
        'repeat_customer_rate': round(repeat_rate, 1),
    }


def _get_vendor_chart_data(vendor, start_date, end_date):
    """Get chart data for vendor analytics"""
    
    # Quality score over time
    quality_history = QualityScore.objects.filter(
        vendor=vendor,
        period_start__gte=start_date
    ).order_by('calculated_at')
    
    quality_chart = [
        {
            'date': score.calculated_at.date().isoformat(),
            'score': float(score.overall_score),
        }
        for score in quality_history
    ]
    
    # Daily performance metrics
    daily_metrics = PerformanceMetrics.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    performance_chart = [
        {
            'date': metric.date.isoformat(),
            'bookings': metric.bookings_received,
            'completion_rate': metric.completion_rate,
            'rating': float(metric.avg_rating),
        }
        for metric in daily_metrics
    ]
    
    return {
        'quality_history': quality_chart,
        'performance_metrics': performance_chart,
    }


def _get_platform_trends(start_date, end_date):
    """Get platform performance trends"""
    
    # Weekly aggregation
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=6), end_date)
        
        week_bookings = Booking.objects.filter(
            created_at__date__range=[current_date, week_end]
        ).count()
        
        week_completed = Booking.objects.filter(
            created_at__date__range=[current_date, week_end],
            status='completed'
        ).count()
        
        week_avg_quality = QualityScore.objects.filter(
            calculated_at__date__range=[current_date, week_end]
        ).aggregate(avg=Avg('overall_score'))['avg'] or 0
        
        trends.append({
            'week_start': current_date.isoformat(),
            'bookings': week_bookings,
            'completion_rate': (week_completed / week_bookings * 100) if week_bookings > 0 else 0,
            'avg_quality_score': round(float(week_avg_quality), 1),
        })
        
        current_date = week_end + timedelta(days=1)
    
    return trends


def _get_vendor_performance_distribution():
    """Get vendor performance distribution"""
    
    # Distribution by quality score ranges
    score_ranges = [
        (90, 100, 'Top Performers'),
        (75, 89, 'Good Performers'),
        (60, 74, 'Average Performers'),
        (0, 59, 'Needs Improvement'),
    ]
    
    distribution = []
    for min_score, max_score, label in score_ranges:
        count = QualityScore.objects.filter(
            overall_score__gte=min_score,
            overall_score__lte=max_score,
            calculated_at__gte=timezone.now() - timedelta(days=30)
        ).values('vendor').distinct().count()
        
        distribution.append({
            'label': label,
            'count': count,
            'range': f"{min_score}-{max_score}",
        })
    
    return distribution


def _get_category_performance(start_date, end_date):
    """Get performance by service category"""
    
    categories = ServiceCategory.objects.all()
    category_performance = []
    
    for category in categories:
        # Get vendor rankings for this category
        rankings = VendorRanking.objects.filter(
            service_category=category,
            period_start__gte=start_date
        )
        
        if rankings.exists():
            avg_quality = rankings.aggregate(avg=Avg('quality_score'))['quality_score__avg'] or 0
            avg_satisfaction = rankings.aggregate(avg=Avg('customer_satisfaction_score'))['customer_satisfaction_score__avg'] or 0
            vendor_count = rankings.values('vendor').distinct().count()
            
            category_performance.append({
                'category': category.name,
                'avg_quality_score': round(float(avg_quality), 1),
                'avg_satisfaction_score': round(float(avg_satisfaction), 1),
                'vendor_count': vendor_count,
            })
    
    return category_performance


def _get_vendor_performance_summary(vendor, start_date, end_date):
    """Get performance summary for vendor dashboard"""
    
    # Latest quality score
    latest_score = QualityScore.objects.filter(
        vendor=vendor
    ).order_by('-calculated_at').first()
    
    # Aggregated metrics
    aggregated = _get_vendor_aggregated_metrics(vendor, start_date, end_date)
    
    # Ranking position
    latest_ranking = VendorRanking.objects.filter(
        vendor=vendor,
        service_category__isnull=True
    ).order_by('-ranking_date').first()
    
    # Performance trend
    scores = QualityScore.objects.filter(
        vendor=vendor,
        calculated_at__gte=timezone.now() - timedelta(days=60)
    ).order_by('calculated_at')
    
    trend = 'stable'
    if len(scores) >= 2:
        recent_avg = sum(score.overall_score for score in scores[-2:]) / 2
        older_avg = sum(score.overall_score for score in scores[:2]) / 2
        
        if recent_avg > older_avg + 5:
            trend = 'improving'
        elif recent_avg < older_avg - 5:
            trend = 'declining'
    
    return {
        'latest_quality_score': latest_score,
        'aggregated_metrics': aggregated,
        'ranking_position': latest_ranking.overall_rank if latest_ranking else None,
        'total_vendors': latest_ranking.total_vendors if latest_ranking else None,
        'performance_trend': trend,
    }


# Smart Vendor Assignment Views

@staff_member_required
def assignment_dashboard(request):
    """Smart Vendor Assignment dashboard"""
    
    # Date range (last 7 days by default)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Assignment statistics
    assignment_stats = _get_assignment_statistics(start_date, end_date)
    
    # Recent assignments
    recent_assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    ).select_related('vendor', 'booking').order_by('-assigned_at')[:20]
    
    # Vendor availability summary
    availability_summary = _get_vendor_availability_summary()
    
    # Assignment performance metrics
    performance_metrics = _get_assignment_performance_metrics(start_date, end_date)
    
    # Assignment alerts
    assignment_alerts = _get_assignment_alerts()
    
    context = {
        'assignment_stats': assignment_stats,
        'recent_assignments': recent_assignments,
        'availability_summary': availability_summary,
        'performance_metrics': performance_metrics,
        'assignment_alerts': assignment_alerts,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/assignment_dashboard.html', context)


@staff_member_required
def vendor_assignment_detail(request, vendor_id):
    """Detailed assignment analytics for a specific vendor"""
    
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Vendor assignments
    assignments = VendorAssignment.objects.filter(
        vendor=vendor,
        assigned_at__date__range=[start_date, end_date]
    ).order_by('-assigned_at')
    
    # Vendor availability
    availability = VendorAvailability.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Vendor workload
    workload = VendorWorkload.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Assignment preferences
    preferences = AssignmentPreference.objects.filter(
        vendor=vendor,
        is_active=True
    )
    
    # Assignment performance
    assignment_performance = _get_vendor_assignment_performance(vendor, start_date, end_date)
    
    # Assignment chart data
    assignment_chart_data = _get_vendor_assignment_chart_data(vendor, start_date, end_date)
    
    context = {
        'vendor': vendor,
        'assignments': assignments[:20],
        'availability': availability[:10],
        'workload': workload[:10],
        'preferences': preferences,
        'assignment_performance': assignment_performance,
        'chart_data': assignment_chart_data,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/vendor_assignment_detail.html', context)


@staff_member_required
def assignment_analytics(request):
    """Assignment analytics and insights"""
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Assignment trends
    assignment_trends = _get_assignment_trends(start_date, end_date)
    
    # Score distribution analysis
    score_distribution = _get_assignment_score_distribution(start_date, end_date)
    
    # Method effectiveness
    method_effectiveness = _get_assignment_method_effectiveness(start_date, end_date)
    
    # Geographic analysis
    geographic_analysis = _get_assignment_geographic_analysis(start_date, end_date)
    
    # Confidence analysis
    confidence_analysis = _get_assignment_confidence_analysis(start_date, end_date)
    
    # Recommendations
    recommendations = _get_assignment_recommendations(start_date, end_date)
    
    context = {
        'assignment_trends': assignment_trends,
        'score_distribution': score_distribution,
        'method_effectiveness': method_effectiveness,
        'geographic_analysis': geographic_analysis,
        'confidence_analysis': confidence_analysis,
        'recommendations': recommendations,
        'date_range': {
            'start': start_date,
            'end': end_date,
        }
    }
    
    return render(request, 'analytics/assignment_analytics.html', context)


@staff_member_required
def assignment_logs(request):
    """Assignment logs and debugging view"""
    
    # Filter parameters
    log_type = request.GET.get('log_type', '')
    vendor_id = request.GET.get('vendor_id', '')
    days = int(request.GET.get('days', 7))
    
    # Date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Base queryset
    logs = AssignmentLog.objects.filter(
        timestamp__range=[start_date, end_date]
    ).select_related('assignment__vendor', 'assignment__booking')
    
    # Apply filters
    if log_type:
        logs = logs.filter(log_type=log_type)
    
    if vendor_id:
        logs = logs.filter(assignment__vendor_id=vendor_id)
    
    # Pagination
    logs = logs.order_by('-timestamp')[:100]
    
    # Available filter options
    log_types = AssignmentLog.objects.values_list('log_type', flat=True).distinct()
    vendors = VendorProfile.objects.filter(status='active').values('id', 'business_name')
    
    context = {
        'logs': logs,
        'log_types': log_types,
        'vendors': vendors,
        'filters': {
            'log_type': log_type,
            'vendor_id': vendor_id,
            'days': days,
        },
        'date_range': {
            'start': start_date.date(),
            'end': end_date.date(),
        }
    }
    
    return render(request, 'analytics/assignment_logs.html', context)


# API endpoints for assignment data
@staff_member_required
def api_assignment_stats(request):
    """API endpoint for assignment statistics"""
    
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    stats = _get_assignment_statistics(start_date, end_date)
    
    return JsonResponse(stats)


@staff_member_required
def api_vendor_availability(request, vendor_id):
    """API endpoint for vendor availability data"""
    
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    availability_data = _get_vendor_availability_data(vendor, start_date, end_date)
    
    return JsonResponse(availability_data)


@staff_member_required
def api_assignment_trends(request):
    """API endpoint for assignment trends data"""
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    trends = _get_assignment_trends(start_date, end_date)
    
    return JsonResponse(trends)


# Auto-assignment action endpoint
@staff_member_required
def auto_assign_pending_bookings(request):
    """Trigger auto-assignment for pending bookings"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Get pending bookings
        pending_bookings = Booking.objects.filter(
            status='pending',
            vendor__isnull=True
        )[:10]  # Limit to 10 for safety
        
        assigned_count = 0
        errors = []
        
        for booking in pending_bookings:
            try:
                assignment = smart_assignment_engine.assign_vendor(booking)
                if assignment:
                    assigned_count += 1
            except Exception as e:
                errors.append(f"Booking {booking.id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'assigned_count': assigned_count,
            'total_processed': len(pending_bookings),
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Helper functions for assignment analytics
def _get_assignment_statistics(start_date, end_date):
    """Get assignment statistics for the date range"""
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    )
    
    total_assignments = assignments.count()
    auto_assignments = assignments.filter(assignment_method='smart_ai').count()
    manual_assignments = assignments.filter(assignment_method='manual').count()
    
    accepted_assignments = assignments.filter(status='accepted').count()
    declined_assignments = assignments.filter(status='declined').count()
    
    # Calculate averages
    avg_score = assignments.aggregate(avg=Avg('total_score'))['avg'] or 0
    avg_confidence = assignments.aggregate(avg=Avg('confidence_level'))['avg'] or 0
    avg_response_time = assignments.exclude(
        vendor_response_time_minutes__isnull=True
    ).aggregate(avg=Avg('vendor_response_time_minutes'))['avg'] or 0
    
    return {
        'total_assignments': total_assignments,
        'auto_assignments': auto_assignments,
        'manual_assignments': manual_assignments,
        'acceptance_rate': (accepted_assignments / total_assignments * 100) if total_assignments > 0 else 0,
        'decline_rate': (declined_assignments / total_assignments * 100) if total_assignments > 0 else 0,
        'auto_assignment_rate': (auto_assignments / total_assignments * 100) if total_assignments > 0 else 0,
        'avg_assignment_score': round(float(avg_score), 1),
        'avg_confidence_level': round(float(avg_confidence), 2),
        'avg_response_time_minutes': round(float(avg_response_time), 1),
    }


def _get_vendor_availability_summary():
    """Get vendor availability summary"""
    
    today = timezone.now().date()
    
    # Vendors available today
    available_today = VendorAvailability.objects.filter(
        date=today,
        status='available'
    ).count()
    
    # Vendors busy today
    busy_today = VendorAvailability.objects.filter(
        date=today,
        status='busy'
    ).count()
    
    # Vendors unavailable today
    unavailable_today = VendorAvailability.objects.filter(
        date=today,
        status='unavailable'
    ).count()
    
    # High utilization vendors (>80% capacity)
    high_utilization = VendorAvailability.objects.filter(
        date=today
    ).annotate(
        utilization=F('current_bookings') * 100.0 / F('max_bookings')
    ).filter(utilization__gte=80).count()
    
    # Average utilization
    avg_utilization = VendorAvailability.objects.filter(
        date=today,
        max_bookings__gt=0
    ).aggregate(
        avg=Avg(F('current_bookings') * 100.0 / F('max_bookings'))
    )['avg'] or 0
    
    return {
        'available_today': available_today,
        'busy_today': busy_today,
        'unavailable_today': unavailable_today,
        'high_utilization_count': high_utilization,
        'avg_utilization': round(float(avg_utilization), 1),
        'total_tracked': available_today + busy_today + unavailable_today,
    }


def _get_assignment_performance_metrics(start_date, end_date):
    """Get assignment performance metrics"""
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    )
    
    # Score distribution
    excellent_scores = assignments.filter(total_score__gte=90).count()
    good_scores = assignments.filter(total_score__gte=80, total_score__lt=90).count()
    average_scores = assignments.filter(total_score__gte=70, total_score__lt=80).count()
    poor_scores = assignments.filter(total_score__lt=70).count()
    
    # Confidence distribution
    high_confidence = assignments.filter(confidence_level__gte=0.8).count()
    medium_confidence = assignments.filter(confidence_level__gte=0.6, confidence_level__lt=0.8).count()
    low_confidence = assignments.filter(confidence_level__lt=0.6).count()
    
    # Response time categories
    fast_responses = assignments.filter(vendor_response_time_minutes__lte=30).count()
    normal_responses = assignments.filter(
        vendor_response_time_minutes__gt=30,
        vendor_response_time_minutes__lte=120
    ).count()
    slow_responses = assignments.filter(vendor_response_time_minutes__gt=120).count()
    
    return {
        'score_distribution': {
            'excellent': excellent_scores,
            'good': good_scores,
            'average': average_scores,
            'poor': poor_scores,
        },
        'confidence_distribution': {
            'high': high_confidence,
            'medium': medium_confidence,
            'low': low_confidence,
        },
        'response_time_distribution': {
            'fast': fast_responses,
            'normal': normal_responses,
            'slow': slow_responses,
        }
    }


def _get_assignment_alerts():
    """Get assignment alerts and issues"""
    
    alerts = []
    
    # High decline rate vendors
    high_decline_vendors = VendorAssignment.objects.filter(
        assigned_at__gte=timezone.now() - timedelta(days=7)
    ).values('vendor').annotate(
        total_assignments=Count('id'),
        declined_assignments=Count('id', filter=Q(status='declined'))
    ).filter(
        total_assignments__gte=3,
        declined_assignments__gte=2
    )[:5]
    
    for vendor_data in high_decline_vendors:
        vendor = VendorProfile.objects.get(id=vendor_data['vendor'])
        decline_rate = vendor_data['declined_assignments'] / vendor_data['total_assignments'] * 100
        
        alerts.append({
            'type': 'high_decline_rate',
            'vendor': vendor,
            'message': f"High decline rate: {decline_rate:.1f}%",
            'severity': 'medium',
        })
    
    # Overloaded vendors
    overloaded_vendors = VendorWorkload.objects.filter(
        date=timezone.now().date(),
        capacity_utilization__gte=100
    )[:5]
    
    for workload in overloaded_vendors:
        alerts.append({
            'type': 'overloaded_vendor',
            'vendor': workload.vendor,
            'message': f"Over capacity: {workload.capacity_utilization:.1f}%",
            'severity': 'high',
        })
    
    # Vendors with no recent availability updates
    stale_availability = VendorAvailability.objects.filter(
        updated_at__lt=timezone.now() - timedelta(days=3)
    ).values('vendor').distinct()[:5]
    
    for vendor_data in stale_availability:
        vendor = VendorProfile.objects.get(id=vendor_data['vendor'])
        alerts.append({
            'type': 'stale_availability',
            'vendor': vendor,
            'message': "Availability data not updated recently",
            'severity': 'low',
        })
    
    return alerts


def _get_vendor_assignment_performance(vendor, start_date, end_date):
    """Get assignment performance for specific vendor"""
    
    assignments = VendorAssignment.objects.filter(
        vendor=vendor,
        assigned_at__date__range=[start_date, end_date]
    )
    
    total_assignments = assignments.count()
    if total_assignments == 0:
        return {
            'total_assignments': 0,
            'acceptance_rate': 0,
            'avg_score': 0,
            'avg_confidence': 0,
            'avg_response_time': 0,
        }
    
    accepted = assignments.filter(status='accepted').count()
    avg_score = assignments.aggregate(avg=Avg('total_score'))['avg'] or 0
    avg_confidence = assignments.aggregate(avg=Avg('confidence_level'))['avg'] or 0
    avg_response_time = assignments.exclude(
        vendor_response_time_minutes__isnull=True
    ).aggregate(avg=Avg('vendor_response_time_minutes'))['avg'] or 0
    
    return {
        'total_assignments': total_assignments,
        'acceptance_rate': (accepted / total_assignments * 100),
        'avg_score': round(float(avg_score), 1),
        'avg_confidence': round(float(avg_confidence), 2),
        'avg_response_time': round(float(avg_response_time), 1),
    }


def _get_vendor_assignment_chart_data(vendor, start_date, end_date):
    """Get chart data for vendor assignment analytics"""
    
    # Daily assignment counts
    daily_assignments = []
    current_date = start_date
    
    while current_date <= end_date:
        assignments_count = VendorAssignment.objects.filter(
            vendor=vendor,
            assigned_at__date=current_date
        ).count()
        
        accepted_count = VendorAssignment.objects.filter(
            vendor=vendor,
            assigned_at__date=current_date,
            status='accepted'
        ).count()
        
        daily_assignments.append({
            'date': current_date.isoformat(),
            'assignments': assignments_count,
            'accepted': accepted_count,
        })
        
        current_date += timedelta(days=1)
    
    # Assignment scores over time
    assignment_scores = VendorAssignment.objects.filter(
        vendor=vendor,
        assigned_at__date__range=[start_date, end_date]
    ).order_by('assigned_at')
    
    score_trend = [
        {
            'date': assignment.assigned_at.date().isoformat(),
            'score': float(assignment.total_score),
            'confidence': float(assignment.confidence_level),
        }
        for assignment in assignment_scores
    ]
    
    return {
        'daily_assignments': daily_assignments,
        'score_trend': score_trend,
    }


def _get_assignment_trends(start_date, end_date):
    """Get assignment trends over time"""
    
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        assignments = VendorAssignment.objects.filter(
            assigned_at__date=current_date
        )
        
        total_count = assignments.count()
        auto_count = assignments.filter(assignment_method='smart_ai').count()
        accepted_count = assignments.filter(status='accepted').count()
        avg_score = assignments.aggregate(avg=Avg('total_score'))['avg'] or 0
        
        trends.append({
            'date': current_date.isoformat(),
            'total_assignments': total_count,
            'auto_assignments': auto_count,
            'accepted_assignments': accepted_count,
            'avg_score': round(float(avg_score), 1),
            'acceptance_rate': (accepted_count / total_count * 100) if total_count > 0 else 0,
        })
        
        current_date += timedelta(days=1)
    
    return trends


def _get_assignment_score_distribution(start_date, end_date):
    """Get assignment score distribution analysis"""
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    )
    
    # Score component analysis
    components = [
        ('quality_score', 'Quality'),
        ('location_score', 'Location'),
        ('availability_score', 'Availability'),
        ('workload_score', 'Workload'),
        ('preference_score', 'Preference'),
    ]
    
    component_stats = {}
    for field, label in components:
        avg_score = assignments.aggregate(avg=Avg(field))[f'{field}__avg'] or 0
        component_stats[label] = round(float(avg_score), 1)
    
    return {
        'component_averages': component_stats,
        'total_assignments': assignments.count(),
    }


def _get_assignment_method_effectiveness(start_date, end_date):
    """Get effectiveness comparison between assignment methods"""
    
    methods = ['smart_ai', 'manual', 'preference_based']
    method_stats = {}
    
    for method in methods:
        assignments = VendorAssignment.objects.filter(
            assigned_at__date__range=[start_date, end_date],
            assignment_method=method
        )
        
        total_count = assignments.count()
        if total_count > 0:
            accepted_count = assignments.filter(status='accepted').count()
            avg_score = assignments.aggregate(avg=Avg('total_score'))['avg'] or 0
            avg_response_time = assignments.exclude(
                vendor_response_time_minutes__isnull=True
            ).aggregate(avg=Avg('vendor_response_time_minutes'))['avg'] or 0
            
            method_stats[method] = {
                'total_assignments': total_count,
                'acceptance_rate': (accepted_count / total_count * 100),
                'avg_score': round(float(avg_score), 1),
                'avg_response_time': round(float(avg_response_time), 1),
            }
    
    return method_stats


def _get_assignment_geographic_analysis(start_date, end_date):
    """Get geographic distribution analysis of assignments"""
    
    # This would be more sophisticated with actual geographic data
    # For now, return a simplified analysis
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    ).select_related('vendor', 'booking')
    
    location_stats = {}
    for assignment in assignments:
        # Simplified - using vendor's city as location
        if hasattr(assignment.vendor, 'city'):
            city = assignment.vendor.city or 'Unknown'
            if city not in location_stats:
                location_stats[city] = {
                    'assignments': 0,
                    'avg_score': 0,
                    'total_score': 0,
                }
            
            location_stats[city]['assignments'] += 1
            location_stats[city]['total_score'] += assignment.total_score
            location_stats[city]['avg_score'] = location_stats[city]['total_score'] / location_stats[city]['assignments']
    
    return location_stats


def _get_assignment_confidence_analysis(start_date, end_date):
    """Get confidence level analysis"""
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    )
    
    confidence_ranges = [
        (0.8, 1.0, 'High Confidence'),
        (0.6, 0.8, 'Medium Confidence'),
        (0.4, 0.6, 'Low Confidence'),
        (0.0, 0.4, 'Very Low Confidence'),
    ]
    
    confidence_stats = {}
    for min_conf, max_conf, label in confidence_ranges:
        filtered_assignments = assignments.filter(
            confidence_level__gte=min_conf,
            confidence_level__lt=max_conf
        )
        
        count = filtered_assignments.count()
        if count > 0:
            accepted_count = filtered_assignments.filter(status='accepted').count()
            acceptance_rate = (accepted_count / count * 100)
        else:
            acceptance_rate = 0
        
        confidence_stats[label] = {
            'count': count,
            'acceptance_rate': round(acceptance_rate, 1),
        }
    
    return confidence_stats


def _get_assignment_recommendations(start_date, end_date):
    """Get AI-generated recommendations for improving assignment system"""
    
    assignments = VendorAssignment.objects.filter(
        assigned_at__date__range=[start_date, end_date]
    )
    
    recommendations = []
    
    # Check overall acceptance rate
    total_assignments = assignments.count()
    if total_assignments > 0:
        accepted = assignments.filter(status='accepted').count()
        acceptance_rate = (accepted / total_assignments * 100)
        
        if acceptance_rate < 70:
            recommendations.append({
                'type': 'acceptance_rate',
                'priority': 'high',
                'title': 'Low Acceptance Rate',
                'description': f'Current acceptance rate is {acceptance_rate:.1f}%. Consider adjusting scoring weights or improving vendor data quality.',
                'action': 'Review scoring algorithm and vendor availability data'
            })
    
    # Check auto-assignment rate
    auto_assignments = assignments.filter(assignment_method='smart_ai').count()
    if total_assignments > 0:
        auto_rate = (auto_assignments / total_assignments * 100)
        
        if auto_rate < 60:
            recommendations.append({
                'type': 'automation',
                'priority': 'medium',
                'title': 'Low Auto-Assignment Rate',
                'description': f'Only {auto_rate:.1f}% of assignments are automated. Consider lowering confidence thresholds.',
                'action': 'Adjust confidence threshold settings'
            })
    
    # Check average confidence level
    avg_confidence = assignments.aggregate(avg=Avg('confidence_level'))['avg'] or 0
    if avg_confidence < 0.7:
        recommendations.append({
            'type': 'confidence',
            'priority': 'medium',
            'title': 'Low Assignment Confidence',
            'description': f'Average confidence level is {avg_confidence:.2f}. Improve data completeness for better predictions.',
            'action': 'Enhance vendor profiles and availability tracking'
        })
    
    return recommendations


def _get_vendor_availability_data(vendor, start_date, end_date):
    """Get vendor availability data for API"""
    
    availability = VendorAvailability.objects.filter(
        vendor=vendor,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    availability_data = [
        {
            'date': avail.date.isoformat(),
            'status': avail.status,
            'utilization_rate': avail.utilization_rate,
            'max_bookings': avail.max_bookings,
            'current_bookings': avail.current_bookings,
        }
        for avail in availability
    ]
    
    return {
        'availability': availability_data,
        'vendor_name': vendor.business_name,
    }
