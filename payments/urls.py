from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment URLs will go here
    # path('', views.PaymentListView.as_view(), name='payment_list'),
    # path('create/<int:booking_id>/', views.CreatePaymentView.as_view(), name='create_payment'),
    # path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
]