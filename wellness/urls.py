from django.urls import path
from . import views

app_name = 'wellness'

urlpatterns = [
    # Home and category views
    path('', views.WellnessHomeView.as_view(), name='wellness_home'),
    path('categories/', views.WellnessCategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.WellnessCategoryDetailView.as_view(), name='category_detail'),
    
    # Program views
    path('programs/', views.WellnessProgramListView.as_view(), name='program_list'),
    path('programs/<slug:slug>/', views.WellnessProgramDetailView.as_view(), name='program_detail'),
    path('programs/<slug:slug>/review/', views.AddReviewView.as_view(), name='add_review'),
    
    # Session views
    path('sessions/', views.WellnessSessionListView.as_view(), name='session_list'),
    path('sessions/<int:pk>/', views.WellnessSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:session_id>/enroll/', views.EnrollSessionView.as_view(), name='enroll_session'),
    
    # User enrollment views
    path('my-enrollments/', views.UserEnrollmentsView.as_view(), name='user_enrollments'),
]