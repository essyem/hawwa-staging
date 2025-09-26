from django.urls import path
from . import views
from . import profile_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Registration URLs
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/mother/', views.MotherRegistrationView.as_view(), name='register_mother'),
    path('register/accommodation/', views.AccommodationProviderRegistrationView.as_view(), name='register_accommodation'),
    path('register/caretaker/', views.CaretakerProviderRegistrationView.as_view(), name='register_caretaker'),
    path('register/wellness/', views.WellnessProviderRegistrationView.as_view(), name='register_wellness'),
    path('register/meditation/', views.MeditationConsultantRegistrationView.as_view(), name='register_meditation'),
    path('register/mental-health/', views.MentalHealthConsultantRegistrationView.as_view(), name='register_mental_health'),
    path('register/food/', views.FoodProviderRegistrationView.as_view(), name='register_food'),
    
    # Profile Management URLs
    path('profile/', profile_views.ProfileDashboardView.as_view(), name='profile'),
    path('profile/edit/', profile_views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/preferences/', profile_views.PreferencesView.as_view(), name='preferences'),
    path('profile/security/', profile_views.SecuritySettingsView.as_view(), name='security_settings'),
    path('profile/bookings/', profile_views.BookingHistoryView.as_view(), name='booking_history'),
    
    # Profile API endpoints
    path('api/profile/analytics/', profile_views.profile_analytics_api, name='profile_analytics_api'),
    path('api/profile/picture/', profile_views.update_profile_picture, name='update_profile_picture'),
    
    # Legacy profile URL (for compatibility)
    path('profile/legacy/', views.ProfileView.as_view(), name='profile_legacy'),
    # Wishlist endpoint (AJAX)
    path('add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),

    # Email OTP flows
    path('verify/email/', views.SendEmailOTPView.as_view(), name='email_verify'),
    path('verify/email/sent/', views.EmailVerificationSentView.as_view(), name='email_verification_sent'),
    path('verify/email/confirm/', views.VerifyEmailOTPView.as_view(), name='verify_email_otp'),
    path('verify/email/resend/', views.ResendEmailOTPView.as_view(), name='resend_email_otp'),
]