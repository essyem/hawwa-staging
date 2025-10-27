from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, Http404, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    DocpoolDocument, DocpoolDepartment, DocpoolDocumentType, 
    DocpoolDocumentBorder, DocpoolReferenceNumber, DocpoolSearchLog,
    DocpoolDocumentAccess
)
from .forms import DocpoolDocumentForm, DocpoolSearchForm, DocpoolAdvancedSearchForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin/staff access"""
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, 'You need administrator privileges to access this page.')
        return redirect('admin_dashboard:dashboard')


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class DocpoolDocumentListView(LoginRequiredMixin, ListView):
    model = DocpoolDocument
    template_name = 'docpool/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        qs = DocpoolDocument.objects.filter(is_active=True).select_related(
            'department', 'document_type', 'border', 'reference_number', 'uploaded_by'
        )
        
        # Get filter parameters
        search = self.request.GET.get('search', '').strip()
        department_id = self.request.GET.get('department')
        document_type_id = self.request.GET.get('document_type')
        border_id = self.request.GET.get('border')
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        access_level = self.request.GET.get('access_level')
        
        # Apply filters
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search) |
                Q(reference_number__reference_number__icontains=search)
            )
        
        if department_id:
            qs = qs.filter(department_id=department_id)
        
        if document_type_id:
            qs = qs.filter(document_type_id=document_type_id)
        
        if border_id:
            qs = qs.filter(border_id=border_id)
        
        if year:
            qs = qs.filter(year=year)
        
        if month:
            qs = qs.filter(month=month)
        
        if access_level:
            qs = qs.filter(access_level=access_level)
        
        # Log search if there's a search query
        if search and len(search) >= 2:
            DocpoolSearchLog.objects.create(
                query=search,
                results_count=qs.count(),
                user=self.request.user,
                ip_address=get_client_ip(self.request),
                department_filter=department_id or '',
                document_type_filter=document_type_id or '',
                year_filter=int(year) if year else None,
                border_filter=border_id or ''
            )
        
        return qs.order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['departments'] = DocpoolDepartment.objects.filter(is_active=True).order_by('code')
        context['document_types'] = DocpoolDocumentType.objects.filter(is_active=True).order_by('code')
        context['borders'] = DocpoolDocumentBorder.objects.filter(is_active=True).order_by('code')
        
        # Add year options
        current_year = timezone.now().year
        context['years'] = list(range(current_year - 5, current_year + 2))
        
        # Add statistics
        context['total_documents'] = DocpoolDocument.objects.filter(is_active=True).count()
        context['departments_count'] = DocpoolDepartment.objects.filter(is_active=True).count()
        context['document_types_count'] = DocpoolDocumentType.objects.filter(is_active=True).count()
        
        # This month statistics
        current_month = timezone.now().month
        current_year = timezone.now().year
        context['this_month_count'] = DocpoolDocument.objects.filter(
            year=current_year,
            month=current_month,
            is_active=True
        ).count()
        
        return context


class DocpoolDocumentDetailView(LoginRequiredMixin, DetailView):
    model = DocpoolDocument
    template_name = 'docpool/document_detail.html'
    context_object_name = 'document'
    
    def get_object(self):
        obj = super().get_object()
        
        # Log document access
        DocpoolDocumentAccess.objects.create(
            document=obj,
            user=self.request.user,
            ip_address=get_client_ip(self.request),
            access_type='view',
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return obj


class DocpoolDocumentCreateView(AdminRequiredMixin, CreateView):
    model = DocpoolDocument
    form_class = DocpoolDocumentForm
    template_name = 'docpool/document_upload.html'
    success_url = reverse_lazy('docpool:document_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, f'Document "{form.instance.title}" uploaded successfully!')
        return super().form_valid(form)


class DocpoolReferenceNumberListView(AdminRequiredMixin, ListView):
    model = DocpoolReferenceNumber
    template_name = 'docpool/reference_list.html'
    context_object_name = 'references'
    paginate_by = 50
    
    def get_queryset(self):
        return DocpoolReferenceNumber.objects.select_related(
            'department', 'document_type', 'created_by'
        ).order_by('-created_at')


@login_required
def document_download(request, pk):
    """Handle document downloads"""
    document = get_object_or_404(DocpoolDocument, pk=pk, is_active=True)
    
    # Check permissions for confidential documents
    if document.is_confidential and not request.user.is_staff:
        raise Http404("Document not found")
    
    # Log download access
    DocpoolDocumentAccess.objects.create(
        document=document,
        user=request.user,
        ip_address=get_client_ip(request),
        access_type='download',
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Return file response
    if document.file:
        response = HttpResponse(document.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
        return response
    else:
        raise Http404("File not found")


@login_required
def search_analytics(request):
    """Analytics dashboard for search patterns"""
    if not request.user.is_staff:
        messages.error(request, 'You need administrator privileges to access analytics.')
        return redirect('docpool:document_list')
    
    # Get analytics data
    recent_searches = DocpoolSearchLog.objects.select_related('user').order_by('-timestamp')[:50]
    
    # Popular search terms (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    popular_terms = DocpoolSearchLog.objects.filter(
        timestamp__gte=thirty_days_ago
    ).values('query').annotate(
        search_count=Count('id')
    ).order_by('-search_count')[:20]
    
    # Search volume by date
    search_volume = DocpoolSearchLog.objects.filter(
        timestamp__gte=thirty_days_ago
    ).extra(
        select={'date': 'date(timestamp)'}
    ).values('date').annotate(
        searches=Count('id')
    ).order_by('date')
    
    context = {
        'recent_searches': recent_searches,
        'popular_terms': popular_terms,
        'search_volume': search_volume,
        'total_searches': DocpoolSearchLog.objects.count(),
        'total_documents': DocpoolDocument.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'docpool/search_analytics.html', context)


# URL patterns will be defined separately
document_list = DocpoolDocumentListView.as_view()
document_detail = DocpoolDocumentDetailView.as_view()
document_upload = DocpoolDocumentCreateView.as_view()
reference_list = DocpoolReferenceNumberListView.as_view()
