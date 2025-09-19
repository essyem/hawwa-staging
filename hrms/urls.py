from django.urls import path, include
from . import views

app_name = 'hrms'

urlpatterns = [
    # Dashboard
    path('', views.HRMSDashboardView.as_view(), name='dashboard'),
    
    # Employee Management
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_add'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/profile/', views.EmployeeProfileView.as_view(), name='employee_profile'),
    
    # Department Management
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_add'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    path('departments/bulk-action/', views.DepartmentBulkActionView.as_view(), name='department_bulk_action'),
    
    # Position Management
    path('positions/', views.PositionListView.as_view(), name='position_list'),
    path('positions/<int:pk>/', views.PositionDetailView.as_view(), name='position_detail'),
    path('positions/add/', views.PositionCreateView.as_view(), name='position_add'),
    
    # Leave Management
    path('leaves/', views.LeaveApplicationListView.as_view(), name='leave_list'),
    path('leaves/<int:pk>/', views.LeaveApplicationDetailView.as_view(), name='leave_detail'),
    path('leaves/apply/', views.LeaveApplicationCreateView.as_view(), name='leave_apply'),
    path('leaves/<int:pk>/approve/', views.LeaveApprovalView.as_view(), name='leave_approve'),
    path('leaves/balance/', views.LeaveBalanceView.as_view(), name='leave_balance'),
    
    # Attendance Management
    path('attendance/', views.AttendanceDashboardView.as_view(), name='attendance_dashboard'),
    path('attendance/clock/', views.ClockInOutView.as_view(), name='clock_inout'),
    path('attendance/my/', views.UserAttendanceView.as_view(), name='user_attendance'),
    path('attendance/list/', views.AttendanceListView.as_view(), name='attendance_list'),
    
    # Training Management
    path('training/', views.TrainingDashboardView.as_view(), name='training_dashboard'),
    path('training/list/', views.TrainingProgramListView.as_view(), name='training_list'),  # Alias for navigation
    path('training/programs/', views.TrainingProgramListView.as_view(), name='training_programs'),
    path('training/programs/create/', views.TrainingProgramCreateView.as_view(), name='training_program_create'),
    path('training/programs/<int:pk>/', views.TrainingProgramDetailView.as_view(), name='training_program_detail'),
    path('training/programs/<int:pk>/edit/', views.TrainingProgramUpdateView.as_view(), name='training_program_update'),
    path('training/enroll/<int:program_id>/', views.TrainingEnrollmentView.as_view(), name='training_enroll'),
    path('training/my-trainings/', views.MyTrainingsView.as_view(), name='my_trainings'),
    
    # Performance Management
    path('performance/', views.PerformanceDashboardView.as_view(), name='performance_dashboard'),
    path('performance/reviews/', views.PerformanceReviewListView.as_view(), name='performance_reviews'),
    path('performance/reviews/<int:pk>/', views.PerformanceReviewDetailView.as_view(), name='performance_review_detail'),
    
    # Payroll Management
    path('payroll/', views.PayrollDashboardView.as_view(), name='payroll_dashboard'),
    path('payroll/list/', views.PayrollPeriodListView.as_view(), name='payroll_list'),  # Alias for navigation
    path('payroll/periods/', views.PayrollPeriodListView.as_view(), name='payroll_periods'),
    path('payroll/periods/<int:pk>/', views.PayrollPeriodDetailView.as_view(), name='payroll_period_detail'),
    path('payroll/my-payslips/', views.MyPayslipsView.as_view(), name='my_payslips'),
    path('payroll/export/', views.PayrollExportView.as_view(), name='payroll_export'),
    path('payroll/create/', views.PayrollCreateView.as_view(), name='payroll_create'),
    path('payroll/<int:pk>/', views.PayrollDetailView.as_view(), name='payroll_detail'),
    path('payroll/<int:pk>/edit/', views.PayrollUpdateView.as_view(), name='payroll_update'),
    path('payroll/<int:pk>/slip/', views.PayrollSlipView.as_view(), name='payroll_slip'),
    path('payroll/bulk-process/', views.PayrollBulkProcessView.as_view(), name='payroll_bulk_process'),
    path('payroll/bulk-action/', views.PayrollBulkActionView.as_view(), name='payroll_bulk_action'),
    path('payroll/approve-pending/', views.PayrollApprovePendingView.as_view(), name='payroll_approve_pending'),
    path('payroll/reports/', views.PayrollReportsView.as_view(), name='payroll_reports'),
    path('payroll/settings/', views.PayrollSettingsView.as_view(), name='payroll_settings'),
    
    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/builder/', views.ReportsView.as_view(), name='report_builder'),  # Placeholder for report builder
    path('reports/scheduler/', views.ReportsView.as_view(), name='report_scheduler'),  # Placeholder for report scheduler
    path('reports/templates/', views.ReportsView.as_view(), name='report_templates'),  # Placeholder for report templates
    path('reports/dashboard-builder/', views.ReportsView.as_view(), name='dashboard_builder'),  # Placeholder for dashboard builder
    path('reports/view/<int:pk>/', views.ReportsView.as_view(), name='report_view'),  # Placeholder for report view
    path('reports/employees/', views.EmployeeReportView.as_view(), name='employee_report'),
    path('reports/employee-roster/', views.EmployeeRosterReportView.as_view(), name='employee_roster_report'),
    path('reports/new-hire/', views.EmployeeReportView.as_view(), name='new_hire_report'),  # New hire report placeholder
    path('reports/termination/', views.EmployeeReportView.as_view(), name='termination_report'),  # Termination report placeholder
    path('reports/birthday/', views.EmployeeReportView.as_view(), name='birthday_report'),  # Birthday report placeholder
    path('reports/department-headcount/', views.EmployeeReportView.as_view(), name='department_headcount_report'),  # Department headcount placeholder
    path('reports/anniversary/', views.EmployeeReportView.as_view(), name='anniversary_report'),  # Anniversary report placeholder
    path('reports/diversity/', views.EmployeeReportView.as_view(), name='diversity_report'),  # Diversity report placeholder
    path('reports/employee-profile/', views.EmployeeReportView.as_view(), name='employee_profile_report'),  # Employee profile report placeholder
    path('reports/attendance/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('reports/attendance-summary/', views.AttendanceReportView.as_view(), name='attendance_summary_report'),  # Attendance summary placeholder
    path('reports/absenteeism/', views.AttendanceReportView.as_view(), name='absenteeism_report'),  # Absenteeism report placeholder
    path('reports/payroll/', views.PayrollReportView.as_view(), name='payroll_report'),
    path('reports/payroll-summary/', views.PayrollReportView.as_view(), name='payroll_summary_report'),  # Payroll summary placeholder
    path('reports/salary-analysis/', views.PayrollReportView.as_view(), name='salary_analysis_report'),  # Salary analysis placeholder
    path('reports/tax/', views.PayrollReportView.as_view(), name='tax_report'),  # Tax report placeholder
    path('reports/deduction/', views.PayrollReportView.as_view(), name='deduction_report'),  # Deduction report placeholder
    path('reports/overtime/', views.PayrollReportView.as_view(), name='overtime_report'),  # Overtime report placeholder
    path('reports/payroll-register/', views.PayrollReportView.as_view(), name='payroll_register_report'),  # Payroll register placeholder
    path('reports/leave/', views.ReportsView.as_view(), name='leave_report'),  # Leave report placeholder
    path('reports/leave-balance/', views.ReportsView.as_view(), name='leave_balance_report'),  # Leave balance placeholder
    path('reports/leave-usage/', views.ReportsView.as_view(), name='leave_usage_report'),  # Leave usage placeholder
    path('reports/leave-calendar/', views.ReportsView.as_view(), name='leave_calendar_report'),  # Leave calendar placeholder
    path('reports/holiday/', views.ReportsView.as_view(), name='holiday_report'),  # Holiday report placeholder
    path('reports/training/', views.ReportsView.as_view(), name='training_report'),  # Training report placeholder
    path('reports/training-completion/', views.ReportsView.as_view(), name='training_completion_report'),  # Training completion placeholder
    path('reports/training-progress/', views.ReportsView.as_view(), name='training_progress_report'),  # Training progress placeholder
    path('reports/skill-gap/', views.ReportsView.as_view(), name='skill_gap_report'),  # Skill gap placeholder
    path('reports/training-cost/', views.ReportsView.as_view(), name='training_cost_report'),  # Training cost placeholder
    path('reports/certification/', views.ReportsView.as_view(), name='certification_report'),  # Certification placeholder
    path('reports/training-feedback/', views.ReportsView.as_view(), name='training_feedback_report'),  # Training feedback placeholder
    
    # Analytics
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('analytics/employees/', views.EmployeeAnalyticsView.as_view(), name='employee_analytics'),
    path('analytics/leave/', views.LeaveAnalyticsView.as_view(), name='leave_analytics'),
    path('analytics/training/', views.TrainingAnalyticsView.as_view(), name='training_analytics'),
    path('analytics/payroll/', views.PayrollAnalyticsView.as_view(), name='payroll_analytics'),
    
    # Custom Reports
    path('reports/custom/', views.CustomReportListView.as_view(), name='custom_report_list'),
    path('reports/custom/create/', views.CustomReportCreateView.as_view(), name='custom_report_create'),
    path('reports/custom/<int:pk>/', views.CustomReportDetailView.as_view(), name='custom_report_view'),
    
    # Scheduled Reports
    path('reports/scheduled/', views.ScheduledReportListView.as_view(), name='scheduled_report_list'),
    path('reports/scheduled/create/', views.ScheduledReportCreateView.as_view(), name='scheduled_report_create'),
    
    # Report Downloads and Export
    path('reports/download/<int:pk>/', views.ReportDownloadView.as_view(), name='download_report'),
    path('reports/export/', views.export_report_ajax, name='export_report_ajax'),
    
    # Employee Profile List
    path('reports/employee-profiles/', views.EmployeeProfileListView.as_view(), name='employee_profile_list'),
    
    # Time & Attendance Management
    path('attendance/', views.AttendanceDashboardView.as_view(), name='attendance_dashboard'),
    path('attendance/user/', views.user_attendance_view, name='user_attendance'),
    path('attendance/clock/', views.ClockInOutView.as_view(), name='clock_inout'),
    path('attendance/list/', views.AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/my-log/', views.MyAttendanceLogView.as_view(), name='my_attendance_log'),
    path('attendance/timesheet/', views.TimeSheetView.as_view(), name='timesheet'),
    path('attendance/reports/', views.AttendanceReportView.as_view(), name='attendance_reports'),
    
    # Attendance API endpoints
    path('attendance/api/status/', views.attendance_status_api, name='attendance_status_api'),
    path('attendance/api/checkin/', views.check_in_api, name='check_in_api'),
    path('attendance/api/checkout/', views.check_out_api, name='check_out_api'),
    
    # Attendance Requests
    path('attendance/requests/', views.AttendanceRequestListView.as_view(), name='attendance_requests'),
    path('attendance/requests/create/', views.AttendanceRequestCreateView.as_view(), name='attendance_request_create'),
    
    # Work Schedules
    path('schedules/', views.WorkScheduleListView.as_view(), name='schedule_list'),
    path('schedules/create/', views.WorkScheduleCreateView.as_view(), name='schedule_create'),
    
    # Vendor Integration
    path('vendor-integration/', views.VendorIntegrationDashboardView.as_view(), name='vendor_integration_dashboard'),
    path('vendor-staff/', views.VendorStaffListView.as_view(), name='vendor_staff_list'),
    path('vendor-staff/create/', views.VendorStaffCreateView.as_view(), name='vendor_staff_create'),
    path('vendor-staff/<int:pk>/', views.VendorStaffDetailView.as_view(), name='vendor_staff_detail'),
    path('service-assignments/', views.ServiceAssignmentListView.as_view(), name='service_assignment_list'),
    
    # API endpoints for AJAX
    path('api/departments/<int:dept_id>/positions/', views.get_department_positions, name='api_department_positions'),
    path('api/employee/<int:emp_id>/leave-balance/', views.get_employee_leave_balance, name='api_leave_balance'),
    
    # REST API endpoints
    path('api/v1/', include(('hrms.api_urls', 'api_v1'), namespace='api_v1')),
]