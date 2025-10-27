from django.urls import path
from . import views

app_name = 'docpool'

urlpatterns = [
    # Main document views
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:pk>/download/', views.document_download, name='document_download'),
    
    # Reference numbers
    path('references/', views.reference_list, name='reference_list'),
    
    # Analytics
    path('analytics/', views.search_analytics, name='search_analytics'),
]