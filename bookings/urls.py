from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Main booking views
    path('', views.BookingListView.as_view(), name='booking_list'),
    path('dashboard/', views.BookingDashboardView.as_view(), name='booking_dashboard'),
    path('new/', views.BookingCreateView.as_view(), name='booking_create'),
    path('new/<int:service_id>/', views.BookingCreateView.as_view(), name='booking_create_service'),
    
    # Booking detail and management
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/update/', views.BookingUpdateView.as_view(), name='booking_update'),
    path('<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking_cancel'),
    path('<int:booking_id>/submit/', views.submit_booking, name='submit_booking'),
    
    # Service booking shortcuts
    path('service/<int:service_id>/', views.book_service, name='book_service'),
    
    # Booking item management (Ajax)
    path('<int:booking_id>/items/add/', views.add_booking_item, name='add_booking_item'),
    path('<int:booking_id>/items/remove/<int:item_id>/', views.remove_booking_item, name='remove_booking_item'),
]