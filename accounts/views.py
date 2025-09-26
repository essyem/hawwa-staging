from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from .forms import (
    LoginForm, UserRegistrationForm, MotherRegistrationForm, AccommodationProviderRegistrationForm,
    CaretakerProviderRegistrationForm, WellnessProviderRegistrationForm,
    MeditationConsultantRegistrationForm, MentalHealthConsultantRegistrationForm,
    FoodProviderRegistrationForm
)
from .models import User
from .profile_models import (
    MotherProfile, AccommodationProviderProfile, CaretakerProviderProfile,
    WellnessProviderProfile, MeditationConsultantProfile, MentalHealthConsultantProfile,
    FoodProviderProfile
)
from .forms import ProfileForm
from django.views.generic.edit import UpdateView
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
import json
from django.core.mail import send_mail
from .utils import send_otp_email
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .forms import EmailOTPRequestForm, EmailOTPVerifyForm
from .models import EmailOTP
import random
from django.views import View
try:
    # preferred import used by django-ratelimit package
    from ratelimit.decorators import ratelimit  # type: ignore
except Exception:
    # Some environments or packaging may expose the package under a different module
    # name (django_ratelimit). Provide a graceful fallback so tests and imports
    # don't fail unexpectedly.
    try:
        from django_ratelimit.decorators import ratelimit  # type: ignore
    except Exception:
        # Re-raise the original import error so callers see the real problem.
        raise
from django.urls import reverse

class RegisterView(TemplateView):
    """View to choose which type of user to register as."""
    template_name = 'accounts/register_choice.html'

class MotherRegistrationView(CreateView):
    """View for mother registration."""
    template_name = 'accounts/register.html'
    form_class = MotherRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Mother')
        context['user_type'] = 'mother'
        return context
    
    def form_valid(self, form):
        user = form.save()
        # Do not auto-login; send verification OTP to email
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            # send multipart OTP email (text + HTML)
            send_otp_email(user.email, code, subject='Your verification code')
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        # Redirect to verification sent page with email prefilled
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class AccommodationProviderRegistrationView(CreateView):
    """View for accommodation provider registration."""
    template_name = 'accounts/register.html'
    form_class = AccommodationProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as an Accommodation Provider')
        context['user_type'] = 'accommodation'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            send_otp_email(user.email, code, subject='Your verification code')
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class CaretakerProviderRegistrationView(CreateView):
    """View for caretaker provider registration."""
    template_name = 'accounts/register.html'
    form_class = CaretakerProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Caretaker Provider')
        context['user_type'] = 'caretaker'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            send_otp_email(user.email, code, subject='Your verification code')
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class WellnessProviderRegistrationView(CreateView):
    """View for wellness provider registration."""
    template_name = 'accounts/register.html'
    form_class = WellnessProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Wellness Service Provider')
        context['user_type'] = 'wellness'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            send_otp_email(user.email, code, subject='Your verification code')
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class MeditationConsultantRegistrationView(CreateView):
    """View for meditation consultant registration."""
    template_name = 'accounts/register.html'
    form_class = MeditationConsultantRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Meditation Consultant')
        context['user_type'] = 'meditation'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            send_otp_email(user.email, code, subject='Your verification code')
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class MentalHealthConsultantRegistrationView(CreateView):
    """View for mental health consultant registration."""
    template_name = 'accounts/register.html'
    form_class = MentalHealthConsultantRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Mental Health Consultant')
        context['user_type'] = 'mental_health'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            subject = 'Your verification code'
            message = f'Your verification code is: {code}\nIt will expire in 5 minutes.'
            send_mail(subject, message, None, [user.email], fail_silently=True)
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class FoodProviderRegistrationView(CreateView):
    """View for food provider registration."""
    template_name = 'accounts/register.html'
    form_class = FoodProviderRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register as a Food Provider')
        context['user_type'] = 'food'
        return context
    
    def form_valid(self, form):
        user = form.save()
        if user.user_type != 'ADMIN':
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            subject = 'Your verification code'
            message = f'Your verification code is: {code}\nIt will expire in 5 minutes.'
            send_mail(subject, message, None, [user.email], fail_silently=True)
        messages.info(self.request, _('A verification code has been sent to your email. Please verify to complete registration.'))
        return redirect(f"{reverse('accounts:email_verification_sent')}?email={user.email}")

class LoginView(FormView):
    """View for user login."""
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core:home')
    
    def form_valid(self, form):
        user = form.get_user()

        # If user email is not verified, send OTP and redirect to verification
        if not user.is_verified:
            # create and send OTP
            code = f"{random.randint(0, 999999):06d}"
            EmailOTP.objects.create(user=user, code=code)
            send_otp_email(user.email, code, subject='Your login verification code')
            messages.info(self.request, _('A verification code has been sent to your email. Please enter it to complete login.'))
            # store the email in session for convenience
            self.request.session['pre_login_email'] = user.email
            # redirect back to login page with a flag so the UI reveals the OTP input
            login_url = reverse('login')
            return redirect(f"{login_url}?show_otp=1&email={user.email}")

        # proceed with normal login
        login(self.request, user)
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
        messages.success(self.request, _('You have successfully logged in.'))
        return super().form_valid(form)

@login_required
def logout_view(request):
    """View for user logout."""
    logout(request)
    messages.success(request, _('You have successfully logged out.'))
    # Use configured logout redirect (can be a URL name like 'core:home')
    return redirect(settings.LOGOUT_REDIRECT_URL)


def add_to_wishlist(request):
    """Simple session-backed wishlist endpoint.

    Expects a POST with JSON body: {"service_id": <int>}.
    Stores a list of service ids in `request.session['wishlist']`.
    Returns JSON {"success": True, "message": "..."} on success.
    For unauthenticated AJAX/JSON callers, returns 401 with {"error":"login_required"}.
    """
    # For AJAX/JSON calls, return a JSON error rather than redirecting to login
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'invalid_method'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    service_id = payload.get('service_id')
    if not service_id:
        return JsonResponse({'error': 'missing_service_id'}, status=400)

    wishlist = request.session.get('wishlist', [])
    # ensure uniqueness
    if service_id not in wishlist:
        wishlist.append(service_id)
        request.session['wishlist'] = wishlist

    return JsonResponse({'success': True, 'message': 'Service added to wishlist', 'wishlist': wishlist})

@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """View for user profile."""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        
        # Get the appropriate profile based on user type
        if user.user_type == 'MOTHER':
            context['profile'] = MotherProfile.objects.get(user=user)
        elif user.user_type == 'ACCOMMODATION':
            context['profile'] = AccommodationProviderProfile.objects.get(user=user)
        elif user.user_type == 'CARETAKER':
            context['profile'] = CaretakerProviderProfile.objects.get(user=user)
        elif user.user_type == 'WELLNESS':
            context['profile'] = WellnessProviderProfile.objects.get(user=user)
        elif user.user_type == 'MEDITATION':
            context['profile'] = MeditationConsultantProfile.objects.get(user=user)
        elif user.user_type == 'MENTAL_HEALTH':
            context['profile'] = MentalHealthConsultantProfile.objects.get(user=user)
        elif user.user_type == 'FOOD':
            context['profile'] = FoodProviderProfile.objects.get(user=user)
            
        return context


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    """View to edit user profile including avatar upload."""
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _('Your profile has been updated.'))
        return super().form_valid(form)


class SendEmailOTPView(FormView):
    """Send a one-time email code to the supplied email address."""
    template_name = 'accounts/email_verification.html'
    form_class = EmailOTPRequestForm
    success_url = reverse_lazy('accounts:email_verification_sent')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For registration flows we may want to allow unknown emails; still send success to avoid enumeration
            user = None

        # If user exists and is ADMIN, do not send OTP (admins use normal login)
        if user and user.user_type == 'ADMIN':
            # behave as if sent but do not create code
            return super().form_valid(form)

        # create a numeric 6-digit code
        code = f"{random.randint(0, 999999):06d}"

        if user:
            EmailOTP.objects.create(user=user, code=code)

        # send email using configured backend (console backend used in dev)
        send_otp_email(email, code, subject='Your verification code')

        return super().form_valid(form)


class EmailVerificationSentView(TemplateView):
    template_name = 'accounts/email_verification_sent.html'


class VerifyEmailOTPView(FormView):
    template_name = 'accounts/verify_otp.html'
    form_class = EmailOTPVerifyForm
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        code = form.cleaned_data['code']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            form.add_error('email', 'No account found for this email')
            return self.form_invalid(form)

        # disallow OTP for ADMIN users
        if user.user_type == 'ADMIN':
            form.add_error(None, 'Administrator accounts must use the standard login flow')
            return self.form_invalid(form)

        # find latest unused matching code
        otps = EmailOTP.objects.filter(user=user, code=code, used=False).order_by('-created_at')
        if not otps.exists():
            form.add_error('code', 'Invalid or expired code')
            return self.form_invalid(form)

        otp = otps.first()
        if not otp.is_valid():
            form.add_error('code', 'Invalid or expired code')
            return self.form_invalid(form)

        # Mark used and mark user as verified
        otp.mark_used()
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        # Log the user in if they are active
        if user.is_active:
            login(self.request, user)

        messages.success(self.request, 'Email verified and logged in successfully')
        return super().form_valid(form)


class ResendEmailOTPView(View):
    """Resend OTP to an email address with simple throttling."""
    @ratelimit(key='post:email', rate='3/h', block=True)
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email') or request.session.get('pre_login_email')
        if not email:
            return JsonResponse({'error': 'missing_email'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # silent success to avoid enumeration
            return JsonResponse({'ok': True})

        code = f"{random.randint(0, 999999):06d}"
        EmailOTP.objects.create(user=user, code=code)
        send_otp_email(email, code, subject='Your verification code')
        return JsonResponse({'ok': True})

    def get_success_url(self):
        return reverse('accounts:profile')
