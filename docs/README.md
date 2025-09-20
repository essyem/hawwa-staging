# Hawwa Business Management Platform - Documentation Hub

Welcome to the comprehensive documentation for the Hawwa Business Management Platform. This guide covers all aspects of using and managing the system for different stakeholders.

## 📚 User Guides

### For Vendors
- **[Vendor Manual](./user-guides/vendor-manual.md)** - Complete guide for service providers
  - Account setup and verification
  - Service catalog management
  - Booking and customer communication
  - Payment processing and financial management
  - Performance monitoring and quality assurance

### For Customers
- **[Customer Guide](./user-guides/customer-guide.md)** - Comprehensive customer manual
  - Account registration and setup
  - Finding and booking services
  - Payment methods and billing
  - Communication with vendors
  - Reviews and feedback system

## 🛠️ Admin Guides

### For System Administrators
- **[Admin Operations Manual](./admin-guides/admin-operations-manual.md)** - Complete administration guide
  - System access and security management
  - Vendor and customer management
  - Financial operations and reporting
  - Platform configuration and monitoring
  - Quality assurance and emergency procedures

## 🎯 Quick Navigation

### New to Hawwa?
1. Start with the [Quick Start Guide](user-guides/quick-start.md)
2. Choose your role: [Customer](user-guides/customer-guide.md) or [Vendor](user-guides/vendor-manual.md)
3. Follow the step-by-step setup instructions

### Need Help?
- **📧 Email Support**: support@hawwa.com
- **📞 Phone Support**: 1-800-HAWWA-HELP
- **💬 Live Chat**: Available in the platform dashboard
- **🎓 Training Sessions**: Contact admin for group training

### System Features Overview

#### For Customers
- ✅ Easy service booking and scheduling
- ✅ Secure payment processing with multiple options
- ✅ Real-time service tracking and updates
- ✅ Direct communication with vendors
- ✅ Review and rating system
- ✅ Booking history and receipts

#### For Vendors
- ✅ Professional profile management
- ✅ Service catalog and pricing control
- ✅ Automated booking notifications
- ✅ Payment processing and tracking
- ✅ Customer communication tools
- ✅ Performance analytics and insights
- ✅ Quality scoring and feedback

#### For Administrators
- ✅ Complete platform oversight
- ✅ Vendor management and approval
- ✅ Financial reporting and analytics
- ✅ Automated workflow management
- ✅ Quality assurance monitoring
- ✅ Customer support tools

## 🚀 Getting Started Checklist

### For New Customers
- [ ] Create account and verify email
- [ ] Complete profile setup
- [ ] Add payment method
- [ ] Browse and book first service
- [ ] Download mobile app (if available)

### For New Vendors
- [ ] Complete vendor application
- [ ] Verify business credentials
- [ ] Set up service catalog
- [ ] Configure pricing and availability
- [ ] Complete profile with photos and descriptions
- [ ] Pass quality verification process

### For New Administrators
- [ ] Access admin panel with credentials
- [ ] Review system configuration
- [ ] Set up workflow templates
- [ ] Configure automation rules
- [ ] Review reporting dashboards
- [ ] Complete admin training

## 📖 Document Structure

Each guide follows a consistent structure:

1. **Overview** - What the document covers
2. **Getting Started** - Initial setup and access
3. **Core Features** - Main functionality walkthrough
4. **Advanced Features** - Power user capabilities
5. **Troubleshooting** - Common issues and solutions
6. **FAQ** - Frequently asked questions
7. **Support** - How to get additional help

## 🔄 Document Updates

This documentation is regularly updated to reflect new features and improvements. Each document includes:

- **Last Updated**: Date of most recent revision
- **Version**: Document version number
- **Changelog**: Summary of recent changes

## 📱 Mobile Access

All documentation is optimized for mobile viewing. You can access these guides on any device through:

- **Web Browser**: docs.hawwa.com
- **Mobile App**: Built-in help section
- **PDF Downloads**: Available for offline viewing

## 🛡️ Security and Privacy

For information about data security, privacy policies, and compliance:
- **[Privacy Policy](legal/privacy-policy.md)**
- **[Terms of Service](legal/terms-of-service.md)**
- **[Security Overview](technical/security.md)**

---

*This documentation is designed to ensure all stakeholders can effectively use the Hawwa platform. If you notice any gaps or need additional information, please contact our documentation team at docs@hawwa.com.*

---

## 🟢 Recent Changes (Sept 20, 2025)

- Frozen current Python dependencies into `requirements-frozen.txt` for a reproducible dev environment.
- Exposed `HAWWA_SETTINGS` to templates via a new context processor (`hawwa/context_processors.py`) and updated header/footer to use the centralized `SUPPORT_EMAIL` and `PHONE_NUMBER` settings.
- Added the `change_management` app (Change Requests, Incidents, Leads) with REST API endpoints, admin dashboard, signals, and tests. See the project checklist for details.

If you rely on `requirements.txt` for deployments, ensure you sync or pin versions from `requirements-frozen.txt` as needed.