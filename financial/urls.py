from django.urls import path
from . import views

app_name = 'financial'

urlpatterns = [
    # Overview
    path('', views.OverviewView.as_view(), name='overview'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<int:pk>/send/', views.send_invoice, name='invoice_send'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<int:pk>/edit/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    
    # Expenses
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('reports/trial-balance/', views.trial_balance_report, name='trial_balance_report'),
    path('reports/cash-flow/', views.cash_flow_report, name='cash_flow_report'),
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),
    
    # API endpoints for AJAX
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/invoice-status-update/', views.invoice_status_update_api, name='invoice_status_update_api'),
    path('api/payment-quick-add/', views.payment_quick_add_api, name='payment_quick_add_api'),
]