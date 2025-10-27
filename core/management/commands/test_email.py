"""
Django management command to test email configuration
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'Test email configuration and send test emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Email address to send test email to',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['simple', 'booking', 'registration'],
            default='simple',
            help='Type of test email to send'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test configuration without sending email'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Testing Email Configuration'))
        self.stdout.write('=' * 50)
        
        # Display current email settings
        self.display_email_settings()
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
            self.test_connection_only()
            return
        
        # Send test email
        to_email = options['to']
        email_type = options['type']
        
        try:
            if email_type == 'simple':
                self.send_simple_test_email(to_email)
            elif email_type == 'booking':
                self.send_booking_test_email(to_email)
            elif email_type == 'registration':
                self.send_registration_test_email(to_email)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Email sending failed: {e}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('✅ Email configuration test completed successfully!')
        )

    def display_email_settings(self):
        """Display current email configuration"""
        self.stdout.write('\n📧 Current Email Settings:')
        self.stdout.write(f'   Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   Host: {getattr(settings, "EMAIL_HOST", "Not set")}')
        self.stdout.write(f'   Port: {getattr(settings, "EMAIL_PORT", "Not set")}')
        self.stdout.write(f'   Use TLS: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
        self.stdout.write(f'   Use SSL: {getattr(settings, "EMAIL_USE_SSL", "Not set")}')
        self.stdout.write(f'   Host User: {getattr(settings, "EMAIL_HOST_USER", "Not set")}')
        self.stdout.write(f'   Default From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'   Subject Prefix: {getattr(settings, "EMAIL_SUBJECT_PREFIX", "Not set")}')
        self.stdout.write(f'   Timeout: {getattr(settings, "EMAIL_TIMEOUT", "Not set")}')
        
        self.stdout.write('\n🏢 Company Settings:')
        self.stdout.write(f'   Company: {getattr(settings, "COMPANY_NAME", "Not set")}')
        self.stdout.write(f'   Support Email: {getattr(settings, "SUPPORT_EMAIL", "Not set")}')
        self.stdout.write(f'   Demo Email: {getattr(settings, "DEMO_EMAIL", "Not set")}')
        self.stdout.write(f'   Sales Email: {getattr(settings, "SALES_EMAIL", "Not set")}')

    def test_connection_only(self):
        """Test email connection without sending"""
        try:
            connection = get_connection()
            connection.open()
            connection.close()
            self.stdout.write(self.style.SUCCESS('✅ Email connection test passed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Email connection failed: {e}'))

    def send_simple_test_email(self, to_email):
        """Send a simple test email"""
        self.stdout.write(f'\n📤 Sending simple test email to: {to_email}')
        
        subject = f'{getattr(settings, "EMAIL_SUBJECT_PREFIX", "")}Email Configuration Test'
        message = f"""
Hello!

This is a test email from the Hawwa platform to verify email configuration.

Email Settings Test Results:
- Email Backend: {settings.EMAIL_BACKEND}
- From Address: {settings.DEFAULT_FROM_EMAIL}
- Company: {getattr(settings, "COMPANY_NAME", "Not set")}
- Support Email: {getattr(settings, "SUPPORT_EMAIL", "Not set")}

If you received this email, your email configuration is working correctly!

Best regards,
{getattr(settings, "COMPANY_NAME", "Hawwa Team")}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Simple test email sent successfully'))

    def send_booking_test_email(self, to_email):
        """Send a booking confirmation test email"""
        self.stdout.write(f'\n📤 Sending booking test email to: {to_email}')
        
        subject = f'{getattr(settings, "EMAIL_SUBJECT_PREFIX", "")}Test Booking Confirmation'
        
        # Create HTML email content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Booking Confirmation</title>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        .header {{ background: #8D1538; color: white; padding: 20px; }}
        .content {{ padding: 20px; }}
        .footer {{ background: #f5f5f5; padding: 15px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🎉 Test Booking Confirmation</h2>
    </div>
    <div class="content">
        <p>Dear Customer,</p>
        <p>This is a <strong>test booking confirmation email</strong> to verify the email functionality of the Hawwa platform.</p>
        
        <h3>Test Booking Details:</h3>
        <ul>
            <li><strong>Booking Number:</strong> TEST-{self.get_test_booking_number()}</li>
            <li><strong>Service:</strong> Email Configuration Test</li>
            <li><strong>Date:</strong> {self.get_current_date()}</li>
            <li><strong>Status:</strong> Email Test Confirmed</li>
        </ul>
        
        <p>If you received this email, your booking email system is working correctly!</p>
        
        <p>For real bookings, contact us at:</p>
        <ul>
            <li>Email: {getattr(settings, "SUPPORT_EMAIL", "support@example.com")}</li>
            <li>Phone: {getattr(settings, "PHONE_NUMBER", "+974 7212 6440")}</li>
        </ul>
    </div>
    <div class="footer">
        <p>Best regards,<br>
        <strong>{getattr(settings, "COMPANY_NAME", "Hawwa Team")}</strong></p>
    </div>
</body>
</html>
        """
        
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=subject,
            body='This is a test booking confirmation email. Please view in HTML.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        self.stdout.write(self.style.SUCCESS('✅ Booking test email sent successfully'))

    def send_registration_test_email(self, to_email):
        """Send a registration test email"""
        self.stdout.write(f'\n📤 Sending registration test email to: {to_email}')
        
        subject = f'{getattr(settings, "EMAIL_SUBJECT_PREFIX", "")}Welcome to Hawwa - Test Registration'
        
        message = f"""
Welcome to {getattr(settings, "COMPANY_NAME", "Hawwa")}!

This is a TEST registration email to verify email functionality.

Your test account details:
- Email: {to_email}
- Registration Date: {self.get_current_date()}
- Platform: Hawwa Wellness Platform

Next Steps (for real registrations):
1. Verify your email address
2. Complete your profile
3. Explore our services

Need help? Contact us:
- Support: {getattr(settings, "SUPPORT_EMAIL", "support@example.com")}
- Demo: {getattr(settings, "DEMO_EMAIL", "demo@example.com")}
- Sales: {getattr(settings, "SALES_EMAIL", "sales@example.com")}

Thank you for testing our email system!

Best regards,
The {getattr(settings, "COMPANY_NAME", "Hawwa")} Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "REGISTRATION_EMAIL", settings.DEFAULT_FROM_EMAIL),
            recipient_list=[to_email],
            fail_silently=False
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Registration test email sent successfully'))

    def get_test_booking_number(self):
        """Generate a test booking number"""
        import datetime
        return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

    def get_current_date(self):
        """Get current date formatted"""
        import datetime
        return datetime.datetime.now().strftime('%B %d, %Y at %H:%M')