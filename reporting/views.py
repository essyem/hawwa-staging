from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .services import AnalyticsService
from .models import AnalyticsMetric, BusinessInsight, ReportTemplate

@staff_member_required
def analytics_dashboard(request):
    """Main analytics dashboard view."""
    analytics = AnalyticsService()
    
    # Get dashboard data
    dashboard_data = analytics.get_dashboard_data()
    
    # Get booking statistics for charts
    from bookings.models import Booking
    booking_stats = {
        'pending': Booking.objects.filter(status='pending').count(),
        'confirmed': Booking.objects.filter(status='confirmed').count(),
        'completed': Booking.objects.filter(status='completed').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'dashboard_metrics': dashboard_data['metrics'],
        'insights': dashboard_data['insights'],
        'booking_stats': booking_stats,
        'last_updated': dashboard_data['last_updated'],
        'title': 'Business Intelligence Dashboard'
    }
    
    return render(request, 'reporting/dashboard.html', context)

@staff_member_required
def dashboard_api(request):
    """API endpoint for real-time dashboard data."""
    analytics = AnalyticsService()
    dashboard_data = analytics.get_dashboard_data()
    
    return JsonResponse(dashboard_data)

@staff_member_required
def metrics_api(request):
    """API endpoint for metrics data."""
    metric_type = request.GET.get('type', 'all')
    period_days = int(request.GET.get('days', 30))
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=period_days)
    
    queryset = AnalyticsMetric.objects.filter(
        date_recorded__range=[start_date, end_date]
    )
    
    if metric_type != 'all':
        queryset = queryset.filter(metric_type=metric_type)
    
    metrics_data = []
    for metric in queryset.order_by('-date_recorded')[:100]:
        metrics_data.append({
            'name': metric.name,
            'type': metric.metric_type,
            'value': float(metric.value),
            'date': metric.date_recorded.isoformat(),
            'aggregation': metric.aggregation_type,
            'metadata': metric.metadata
        })
    
    return JsonResponse({'metrics': metrics_data})

@staff_member_required
def insights_api(request):
    """API endpoint for business insights."""
    priority = request.GET.get('priority', 'all')
    acknowledged = request.GET.get('acknowledged', 'false') == 'true'
    
    queryset = BusinessInsight.objects.filter(
        is_active=True,
        is_acknowledged=acknowledged
    )
    
    if priority != 'all':
        queryset = queryset.filter(priority=priority)
    
    insights_data = []
    for insight in queryset.order_by('-priority', '-created_at')[:50]:
        insights_data.append({
            'id': insight.id,
            'title': insight.title,
            'description': insight.description,
            'type': insight.insight_type,
            'priority': insight.priority,
            'confidence': float(insight.confidence_score),
            'actions': insight.recommended_actions,
            'acknowledged': insight.is_acknowledged,
            'created_at': insight.created_at.isoformat()
        })
    
    return JsonResponse({'insights': insights_data})

@staff_member_required
def generate_report_api(request):
    """API endpoint for generating reports."""
    if request.method == 'POST':
        analytics = AnalyticsService()
        
        # Generate comprehensive report
        report = analytics.generate_comprehensive_report()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Report generated successfully',
            'metrics_count': (
                len(report['financial_metrics']) + 
                len(report['booking_metrics']) + 
                len(report['customer_metrics']) + 
                len(report['service_metrics'])
            ),
            'insights_count': len(report['business_insights']),
            'generated_at': report['generation_time'].isoformat()
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
