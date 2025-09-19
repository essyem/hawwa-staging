from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Avg
from .models import (
    ServiceCategory,
    Service,
    AccommodationService,
    HomeCareService,
    WellnessService,
    NutritionService,
    ServiceReview
)
from .forms import ServiceSearchForm, ServiceReviewForm, ServiceInquiryForm


class ServiceListView(ListView):
    """View for listing services with search and filter functionality."""
    model = Service
    template_name = 'services/list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_form(self):
        """Create and return the search form."""
        if not hasattr(self, '_form'):
            categories = ServiceCategory.objects.all()
            initial = {}
            
            self._form = ServiceSearchForm(
                self.request.GET or None,
                categories=categories,
                initial=initial
            )
        return self._form
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get search form
        form = self.get_form()
        
        if form.is_valid():
            # Search query
            query = form.cleaned_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query)
                )
            
            # Category filter
            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(category_id=category)
            
            # Price range filter
            min_price = form.cleaned_data.get('min_price')
            if min_price is not None:
                queryset = queryset.filter(price__gte=min_price)
                
            max_price = form.cleaned_data.get('max_price')
            if max_price is not None:
                queryset = queryset.filter(price__lte=max_price)
            
            # Sorting
            sort_by = form.cleaned_data.get('sort_by')
            if sort_by == 'price_low':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_high':
                queryset = queryset.order_by('-price')
            elif sort_by == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'name':
                queryset = queryset.order_by('name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use the same form instance
        context['form'] = self.get_form()
        context['categories'] = ServiceCategory.objects.all()
        
        # Add featured services
        context['featured_services'] = Service.objects.filter(featured=True)[:4]
        
        return context


class ServiceDetailView(DetailView):
    """View for displaying service details."""
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_object()
        
        # Add related services
        related_services = Service.objects.filter(
            category=service.category
        ).exclude(id=service.id)[:4]
        context['related_services'] = related_services
        
        # Add reviews with average rating
        reviews = service.reviews.filter(is_public=True).order_by('-created_at')
        context['reviews'] = reviews
        
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        context['avg_rating'] = avg_rating
        context['star_percentage'] = (avg_rating / 5) * 100
        
        # Review form for logged in users
        if self.request.user.is_authenticated:
            # Check if user already reviewed this service
            user_review = ServiceReview.objects.filter(
                service=service, user=self.request.user
            ).first()
            
            if user_review:
                context['user_review'] = user_review
            else:
                context['review_form'] = ServiceReviewForm()
        
        # Service inquiry form
        context['inquiry_form'] = ServiceInquiryForm(service_id=service.id)
        
        # Get specific service details based on service type
        if hasattr(service, 'accommodationservice'):
            context['specific_service'] = service.accommodationservice
            context['service_type'] = 'accommodation'
        elif hasattr(service, 'homecareservice'):
            context['specific_service'] = service.homecareservice
            context['service_type'] = 'homecare'
        elif hasattr(service, 'wellnessservice'):
            context['specific_service'] = service.wellnessservice
            context['service_type'] = 'wellness'
        elif hasattr(service, 'nutritionservice'):
            context['specific_service'] = service.nutritionservice
            context['service_type'] = 'nutrition'
        
        return context


class AddServiceReviewView(LoginRequiredMixin, CreateView):
    """View for adding a review to a service."""
    model = ServiceReview
    form_class = ServiceReviewForm
    
    def form_valid(self, form):
        service = get_object_or_404(Service, slug=self.kwargs['slug'])
        
        # Check if user already reviewed this service
        if ServiceReview.objects.filter(service=service, user=self.request.user).exists():
            messages.error(self.request, _("You have already reviewed this service."))
            return redirect('services:service_detail', slug=service.slug)
        
        review = form.save(commit=False)
        review.service = service
        review.user = self.request.user
        review.save()
        
        messages.success(self.request, _("Your review has been submitted successfully."))
        return redirect('services:service_detail', slug=service.slug)
    
    def form_invalid(self, form):
        messages.error(self.request, _("There was an error submitting your review."))
        return redirect('services:service_detail', slug=self.kwargs['slug'])


class ServiceInquiryView(LoginRequiredMixin, FormView):
    """View for submitting service inquiries."""
    form_class = ServiceInquiryForm
    template_name = 'services/service_inquiry.html'
    
    def get_success_url(self):
        return reverse('services:inquiry_success')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'slug' in self.kwargs:
            service = get_object_or_404(Service, slug=self.kwargs['slug'])
            kwargs['service_id'] = service.id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'slug' in self.kwargs:
            service = get_object_or_404(Service, slug=self.kwargs['slug'])
            context['service'] = service
        return context
    
    def form_valid(self, form):
        # In a real application, this would save the inquiry to database
        # and/or send email notifications
        
        # For now, just add success message
        messages.success(self.request, _("Your inquiry has been submitted successfully. We will contact you shortly."))
        return super().form_valid(form)


class ServiceInquirySuccessView(TemplateView):
    """View displayed after successful inquiry submission."""
    template_name = 'services/inquiry_success.html'


class ServiceCategoryView(ListView):
    """View for displaying services by category."""
    model = Service
    template_name = 'services/service_category.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(ServiceCategory, slug=self.kwargs['slug'])
        return Service.objects.filter(category=self.category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class AccommodationServiceListView(ListView):
    """View for listing accommodation services."""
    model = AccommodationService
    template_name = 'services/accommodation_list.html'
    context_object_name = 'services'
    paginate_by = 9
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_type'] = 'accommodation'
        context['service_title'] = _('Accommodation Services')
        return context


class HomeCareServiceListView(ListView):
    """View for listing home care services."""
    model = HomeCareService
    template_name = 'services/homecare_list.html'
    context_object_name = 'services'
    paginate_by = 9
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_type'] = 'homecare'
        context['service_title'] = _('Home Care Services')
        return context


class WellnessServiceListView(ListView):
    """View for listing wellness services."""
    model = WellnessService
    template_name = 'services/wellness_list.html'
    context_object_name = 'services'
    paginate_by = 9
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_type'] = 'wellness'
        context['service_title'] = _('Wellness Services')
        return context


class NutritionServiceListView(ListView):
    """View for listing nutrition services."""
    model = NutritionService
    template_name = 'services/nutrition_list.html'
    context_object_name = 'services'
    paginate_by = 9
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_type'] = 'nutrition'
        context['service_title'] = _('Nutrition Services')
        return context
