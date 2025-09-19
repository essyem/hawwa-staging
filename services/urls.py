from django.urls import path
from .views import (
    ServiceListView,
    ServiceDetailView,
    AddServiceReviewView,
    ServiceInquiryView,
    ServiceInquirySuccessView,
    ServiceCategoryView,
    AccommodationServiceListView,
    HomeCareServiceListView,
    WellnessServiceListView,
    NutritionServiceListView
)

app_name = 'services'

urlpatterns = [
    # Main service views
    path('', ServiceListView.as_view(), name='service_list'),
    path('service/<slug:slug>/', ServiceDetailView.as_view(), name='service_detail'),
    path('service/<slug:slug>/review/', AddServiceReviewView.as_view(), name='add_review'),
    path('service/<slug:slug>/inquiry/', ServiceInquiryView.as_view(), name='inquiry'),
    path('inquiry/success/', ServiceInquirySuccessView.as_view(), name='inquiry_success'),
    path('category/<slug:slug>/', ServiceCategoryView.as_view(), name='service_category'),
    
    # Specialized service type views
    path('accommodation/', AccommodationServiceListView.as_view(), name='accommodation_list'),
    path('homecare/', HomeCareServiceListView.as_view(), name='homecare_list'),
    path('wellness/', WellnessServiceListView.as_view(), name='wellness_list'),
    path('nutrition/', NutritionServiceListView.as_view(), name='nutrition_list'),
]