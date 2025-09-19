from django import forms
from django.contrib.auth.models import User
from .models import (
    EmployeeProfile, 
    LeaveApplication,
    LeaveType,
    EmployeeEducation,
    EmployeeDocument,
    EducationLevel,
    DocumentType
)


class EmployeeCreateForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'employee_id', 'date_of_birth', 'place_of_birth', 'nationality',
            'qatar_id', 'qatar_id_expiry', 'passport_number', 'passport_expiry', 
            'passport_issue_country', 'national_id',
            'gender', 'marital_status', 'blood_group', 'personal_email',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'current_address', 'permanent_address',
            'department', 'position', 'grade', 'employment_type', 'work_location',
            'hire_date', 'basic_salary', 'housing_allowance', 'transport_allowance',
            'other_allowances', 'photo'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'qatar_id_expiry': forms.DateInput(attrs={'type': 'date'}),
            'passport_expiry': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'current_address': forms.Textarea(attrs={'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'rows': 3}),
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            if self.fields[field].widget.__class__.__name__ == 'Select':
                self.fields[field].widget.attrs['class'] = 'form-select'
            elif self.fields[field].widget.__class__.__name__ == 'Textarea':
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self, commit=True):
        # Create the User first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        
        # Create the EmployeeProfile
        employee = super().save(commit=False)
        employee.user = user
        
        if commit:
            employee.save()
        
        return employee


class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = [
            'date_of_birth', 'place_of_birth', 'nationality',
            'qatar_id', 'qatar_id_expiry', 'passport_number', 'passport_expiry', 
            'passport_issue_country', 'national_id',
            'gender', 'marital_status', 'blood_group', 'personal_email',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'current_address', 'permanent_address',
            'department', 'position', 'grade', 'employment_type', 'work_location',
            'basic_salary', 'housing_allowance', 'transport_allowance',
            'other_allowances', 'status', 'photo'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'qatar_id_expiry': forms.DateInput(attrs={'type': 'date'}),
            'passport_expiry': forms.DateInput(attrs={'type': 'date'}),
            'current_address': forms.Textarea(attrs={'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'rows': 3}),
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            if self.fields[field].widget.__class__.__name__ == 'Select':
                self.fields[field].widget.attrs['class'] = 'form-select'
            elif self.fields[field].widget.__class__.__name__ == 'Textarea':
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'


class EmployeeEducationForm(forms.ModelForm):
    class Meta:
        model = EmployeeEducation
        fields = [
            'education_level', 'institution_name', 'field_of_study', 'degree_title',
            'start_month', 'start_year', 'end_month', 'end_year', 'is_current',
            'grade_gpa', 'country', 'certificate', 'transcript'
        ]
        widgets = {
            'start_year': forms.NumberInput(attrs={'min': 1950, 'max': 2030}),
            'end_year': forms.NumberInput(attrs={'min': 1950, 'max': 2030}),
            'certificate': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'}),
            'transcript': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes and customize fields
        for field in self.fields:
            if self.fields[field].widget.__class__.__name__ == 'Select':
                self.fields[field].widget.attrs['class'] = 'form-select'
            elif self.fields[field].widget.__class__.__name__ in ['FileInput']:
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Make end fields optional when is_current is True
        self.fields['end_month'].required = False
        self.fields['end_year'].required = False


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = [
            'document_type', 'title', 'document_number', 'file',
            'issue_date', 'expiry_date', 'notes'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'file': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            if self.fields[field].widget.__class__.__name__ == 'Select':
                self.fields[field].widget.attrs['class'] = 'form-select'
            elif self.fields[field].widget.__class__.__name__ == 'Textarea':
                self.fields[field].widget.attrs['class'] = 'form-control'
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Make expiry_date required only for documents that have expiry
        if hasattr(self.instance, 'document_type') and self.instance.document_type:
            if not self.instance.document_type.has_expiry:
                self.fields['expiry_date'].required = False


# Multiple forms for adding education and documents during employee creation
EmployeeEducationFormSet = forms.inlineformset_factory(
    EmployeeProfile, 
    EmployeeEducation, 
    form=EmployeeEducationForm,
    extra=1, 
    can_delete=True
)

EmployeeDocumentFormSet = forms.inlineformset_factory(
    EmployeeProfile, 
    EmployeeDocument, 
    form=EmployeeDocumentForm,
    extra=1, 
    can_delete=True
)


class LeaveApplicationForm(forms.ModelForm):
    """Form for applying leave with substitution"""
    
    class Meta:
        model = LeaveApplication
        fields = [
            'leave_type', 'start_date', 'end_date', 'days_requested', 
            'reason', 'substitute_employee', 'substitute_notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'days_requested': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.5'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide reason for leave...'
            }),
            'substitute_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe work handover and responsibilities to be covered...'
            }),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'substitute_employee': forms.Select(attrs={'class': 'form-select'})
        }
        
    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        # Filter substitute employees (exclude the applicant)
        if employee:
            self.fields['substitute_employee'].queryset = EmployeeProfile.objects.exclude(
                id=employee.id
            ).select_related('department', 'user').order_by('department__name', 'user__first_name')
            
        # Custom labels and help texts
        self.fields['substitute_employee'].empty_label = "Select substitute employee..."
        self.fields['substitute_employee'].help_text = "Choose an employee who will cover your responsibilities"
        self.fields['substitute_notes'].help_text = "Provide details about work handover and specific tasks to be covered"
        
        # Group substitute employees by department
        substitute_choices = []
        if employee:
            departments = {}
            for emp in self.fields['substitute_employee'].queryset:
                dept_name = emp.department.name if emp.department else 'No Department'
                if dept_name not in departments:
                    departments[dept_name] = []
                departments[dept_name].append((emp.id, f"{emp.user.get_full_name()} ({emp.employee_id})"))
            
            # Create grouped choices
            for dept_name, employees in departments.items():
                substitute_choices.append((dept_name, employees))
                
        if substitute_choices:
            self.fields['substitute_employee'].widget = forms.Select(
                choices=[('', 'Select substitute employee...')] + 
                [(dept, employees) for dept, employees in substitute_choices],
                attrs={'class': 'form-select'}
            )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        days_requested = cleaned_data.get('days_requested')
        substitute_employee = cleaned_data.get('substitute_employee')
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be before start date.")
                
        # Calculate business days and validate
        if start_date and end_date and days_requested:
            from datetime import timedelta
            business_days = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday to Friday
                    business_days += 1
                current_date += timedelta(days=1)
            
            if days_requested > business_days:
                raise forms.ValidationError(
                    f"Days requested ({days_requested}) cannot exceed business days in range ({business_days})."
                )
        
        # Substitute employee is required for leaves > 3 days
        if days_requested and days_requested > 3 and not substitute_employee:
            raise forms.ValidationError(
                "A substitute employee must be assigned for leaves longer than 3 days."
            )
            
        return cleaned_data

