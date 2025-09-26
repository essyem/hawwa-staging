from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_otp_email(to_email: str, code: str, subject: str = 'Your verification code') -> None:
    """Send a multipart (text + HTML) OTP email to `to_email`.

    Templates:
      - `emails/otp_email.txt`
      - `emails/otp_email.html`
    """
    context = {
        'code': code,
        'support_email': getattr(settings, 'HAWWA_SETTINGS', {}).get('SUPPORT_EMAIL', None),
        'app_name': getattr(settings, 'HAWWA_SETTINGS', {}).get('COMPANY_NAME', ''),
    }

    text_body = render_to_string('emails/otp_email.txt', context)
    html_body = render_to_string('emails/otp_email.html', context)

    msg = EmailMultiAlternatives(subject=subject, body=text_body, to=[to_email])
    msg.attach_alternative(html_body, 'text/html')
    # Use settings-configured email backend; fail silently in non-critical flows
    msg.send(fail_silently=True)
