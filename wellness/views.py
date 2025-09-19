from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import (
    WellnessCategory, 
    WellnessProgram, 
    WellnessSession, 
    WellnessEnrollment,
    WellnessReview
)

class WellnessHomeView(TemplateView):
    """Homepage for wellness section"""
    template_name = "wellness/wellness_home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_programs'] = WellnessProgram.objects.filter(
            status='active', 
            featured=True
        )[:4]
        context['categories'] = WellnessCategory.objects.filter(is_active=True)[:6]
        context['upcoming_sessions'] = WellnessSession.objects.filter(
            status='scheduled'
        ).order_by('date', 'start_time')[:3]
        return context

class WellnessCategoryListView(ListView):
    """List all wellness categories"""
    model = WellnessCategory
    template_name = "wellness/category_list.html"
    context_object_name = "categories"
    queryset = WellnessCategory.objects.filter(is_active=True)

class WellnessCategoryDetailView(DetailView):
    """Show details of a wellness category and its programs"""
    model = WellnessCategory
    template_name = "wellness/category_detail.html"
    context_object_name = "category"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programs'] = self.object.programs.filter(status='active')
        return context

class WellnessProgramListView(ListView):
    """List all wellness programs"""
    model = WellnessProgram
    template_name = "wellness/program_list.html"
    context_object_name = "programs"
    paginate_by = 9
    
    def get_queryset(self):
        queryset = WellnessProgram.objects.filter(status='active')
        
        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(short_description__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = WellnessCategory.objects.filter(is_active=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context

class WellnessProgramDetailView(DetailView):
    """Show details of a wellness program"""
    model = WellnessProgram
    template_name = "wellness/program_detail.html"
    context_object_name = "program"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upcoming_sessions'] = self.object.sessions.filter(
            status='scheduled',
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')
        
        # Get related programs in same category
        context['related_programs'] = WellnessProgram.objects.filter(
            category=self.object.category,
            status='active'
        ).exclude(pk=self.object.pk)[:3]
        
        # Check if user is enrolled
        if self.request.user.is_authenticated:
            context['user_enrolled'] = WellnessEnrollment.objects.filter(
                user=self.request.user,
                program=self.object,
                status='enrolled'
            ).exists()
            
            # Check if user has reviewed
            context['user_review'] = WellnessReview.objects.filter(
                user=self.request.user,
                program=self.object
            ).first()
        
        # Get reviews
        context['reviews'] = self.object.reviews.all()
        context['avg_rating'] = self.object.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        return context

class WellnessSessionListView(ListView):
    """List all scheduled wellness sessions"""
    model = WellnessSession
    template_name = "wellness/session_list.html"
    context_object_name = "sessions"
    paginate_by = 10
    
    def get_queryset(self):
        return WellnessSession.objects.filter(
            status='scheduled',
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')

class WellnessSessionDetailView(DetailView):
    """Show details of a wellness session"""
    model = WellnessSession
    template_name = "wellness/session_detail.html"
    context_object_name = "session"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user is enrolled in this session
        if self.request.user.is_authenticated:
            context['user_enrolled'] = WellnessEnrollment.objects.filter(
                user=self.request.user,
                session=self.object,
                status='enrolled'
            ).exists()
            
        # Get number of participants
        context['participant_count'] = self.object.participants.filter(status='enrolled').count()
        context['spots_left'] = max(0, self.object.max_participants - context['participant_count'])
        
        return context

class EnrollSessionView(LoginRequiredMixin, CreateView):
    """Enroll in a wellness session"""
    model = WellnessEnrollment
    template_name = "wellness/enroll_session.html"
    fields = ['notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.kwargs.get('session_id')
        context['session'] = get_object_or_404(WellnessSession, pk=session_id)
        return context
    
    def form_valid(self, form):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(WellnessSession, pk=session_id)
        
        # Check if session is full
        participant_count = session.participants.filter(status='enrolled').count()
        if participant_count >= session.max_participants:
            messages.error(self.request, _("Sorry, this session is already full."))
            return redirect(session.get_absolute_url())
        
        # Create enrollment
        enrollment = form.save(commit=False)
        enrollment.user = self.request.user
        enrollment.session = session
        enrollment.program = session.program
        enrollment.status = 'enrolled'
        enrollment.save()
        
        messages.success(self.request, _("You have successfully enrolled in this session."))
        return redirect(session.get_absolute_url())

class UserEnrollmentsView(LoginRequiredMixin, ListView):
    """Show user's wellness enrollments"""
    model = WellnessEnrollment
    template_name = "wellness/user_enrollments.html"
    context_object_name = "enrollments"
    
    def get_queryset(self):
        return WellnessEnrollment.objects.filter(
            user=self.request.user
        ).select_related('program', 'session').order_by('-enrolled_at')

class AddReviewView(LoginRequiredMixin, CreateView):
    """Add a review for a wellness program"""
    model = WellnessReview
    template_name = "wellness/add_review.html"
    fields = ['rating', 'comment']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program_slug = self.kwargs.get('slug')
        context['program'] = get_object_or_404(WellnessProgram, slug=program_slug)
        return context
    
    def form_valid(self, form):
        program_slug = self.kwargs.get('slug')
        program = get_object_or_404(WellnessProgram, slug=program_slug)
        
        # Check if user already reviewed this program
        existing_review = WellnessReview.objects.filter(
            user=self.request.user,
            program=program
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = form.cleaned_data['rating']
            existing_review.comment = form.cleaned_data['comment']
            existing_review.save()
            messages.success(self.request, _("Your review has been updated."))
        else:
            # Create new review
            review = form.save(commit=False)
            review.user = self.request.user
            review.program = program
            review.save()
            messages.success(self.request, _("Thank you for your review."))
        
        return redirect(program.get_absolute_url())
