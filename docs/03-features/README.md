# Feature Documentation

Module-specific documentation for HAWWA features.

## 📦 Modules

### [Admin Portal](admin-portal/)
Administrative interface for system management
- User management
- System configuration
- Dashboard and analytics
- [Documentation](admin-portal/ADMIN_PORTAL_README.md)

### [Bookings System](bookings/)
Comprehensive booking management system
- Service booking
- Email notifications
- Payment integration
- [Email Fix Documentation](bookings/BOOKING_EMAIL_FIX.md)

### [Change Management](change-management/)
IT change management and incident tracking
- Change requests
- Approval workflows
- Incident management
- Activity tracking
- [Frontend Setup](change-management/CHANGE_MANAGEMENT_FRONTEND_SETUP.md)

### [HRMS Module](hrms/)
Human Resource Management System
- Employee management
- Attendance tracking
- Leave management
- Payroll processing
- Performance reviews
- Training management
- [DocPool Integration](hrms/HRMS_DOCPOOL_INTEGRATION_ANALYSIS.md)

### [Navigation](navigation/)
System navigation and UI components
- Sidebar navigation
- Module organization
- User experience
- [Navigation Behavior](navigation/NAVIGATION_BEHAVIOR.md)

## 🎯 Module Status

| Module | Status | Documentation | Tests |
|--------|--------|---------------|-------|
| Admin Portal | ✅ Active | Complete | Partial |
| Bookings | ✅ Active | Complete | Partial |
| Change Management | ✅ Active | Complete | In Progress |
| HRMS | ✅ Active | Complete | In Progress |
| Navigation | ✅ Active | Complete | N/A |
| Financial | 🚧 In Progress | Partial | Pending |
| Analytics | 🚧 In Progress | Partial | Pending |
| AI Buddy | 🚧 In Progress | Partial | Pending |
| Wellness | 📋 Planned | N/A | N/A |
| Vendors | 📋 Planned | N/A | N/A |

## 📚 Common Patterns

### URL Patterns
```python
# Module URLs
urlpatterns = [
    path('', views.dashboard, name='module_dashboard'),
    path('list/', views.item_list, name='module_list'),
    path('create/', views.item_create, name='module_create'),
    path('<int:pk>/', views.item_detail, name='module_detail'),
    path('<int:pk>/edit/', views.item_edit, name='module_edit'),
    path('<int:pk>/delete/', views.item_delete, name='module_delete'),
]
```

### View Structure
```python
# Class-based views for CRUD operations
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'module/item_list.html'
    context_object_name = 'items'
```

### Template Organization
```
templates/
└── module_name/
    ├── module_base.html          # Base template
    ├── dashboard.html             # Dashboard view
    ├── item_list.html             # List view
    ├── item_detail.html           # Detail view
    └── item_form.html             # Create/Edit form
```

## 🔧 Adding a New Feature

1. **Create Module Structure**
```bash
cd /root/hawwa
python manage.py startapp new_module
```

2. **Add to INSTALLED_APPS**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'new_module',
]
```

3. **Create Documentation**
```bash
mkdir -p docs/03-features/new-module
touch docs/03-features/new-module/README.md
```

4. **Add to Navigation**
```python
# settings.py
MODULE_SIDEBAR = [
    {
        'label': 'New Module',
        'icon': 'fas fa-icon',
        'url_name': 'new_module:dashboard',
        'permission': 'new_module.view_item',
    },
]
```

## 📖 Documentation Guidelines

Each module should have:
- [ ] README.md with overview
- [ ] Feature list and capabilities
- [ ] Setup/configuration instructions
- [ ] API documentation (if applicable)
- [ ] Known issues and limitations
- [ ] Future enhancements

## 🆘 Support

For module-specific questions:
- Check module documentation first
- Review code comments
- Search for similar implementations
- Contact module owner
- Create GitHub issue
