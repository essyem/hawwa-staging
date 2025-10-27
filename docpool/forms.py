from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, Row, Column, Submit, HTML
from crispy_forms.bootstrap import InlineRadios
from .models import (
    DocpoolDocument, DocpoolDepartment, DocpoolDocumentType, 
    DocpoolDocumentBorder, DocpoolDocumentCategory, DocpoolDocumentSubCategory
)


class DocpoolDocumentForm(forms.ModelForm):
    class Meta:
        model = DocpoolDocument
        fields = [
            'file', 'title', 'description', 'keywords', 
            'year', 'month', 'department', 'document_type', 'border',
            'category', 'subcategory', 
            'access_level', 'is_confidential', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'keywords': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter keywords separated by commas'}),
            'year': forms.NumberInput(attrs={'min': 2020, 'max': 2030}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set current year as default
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['year'].initial = timezone.now().year
            self.fields['month'].initial = timezone.now().month
        
        # Setup crispy forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Document File',
                Field('file', css_class='form-control'),
            ),
            Fieldset(
                'Basic Information',
                Row(
                    Column('title', css_class='form-group col-md-8 mb-0'),
                    Column('year', css_class='form-group col-md-4 mb-0'),
                ),
                'description',
                'keywords',
            ),
            Fieldset(
                'Classification',
                Row(
                    Column('department', css_class='form-group col-md-4 mb-0'),
                    Column('document_type', css_class='form-group col-md-4 mb-0'),
                    Column('border', css_class='form-group col-md-4 mb-0'),
                ),
                Row(
                    Column('month', css_class='form-group col-md-6 mb-0'),
                    Column('access_level', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Legacy Classification (Optional)',
                Row(
                    Column('category', css_class='form-group col-md-6 mb-0'),
                    Column('subcategory', css_class='form-group col-md-6 mb-0'),
                ),
                css_class='mt-3'
            ),
            Fieldset(
                'Security & Status',
                Row(
                    Column(
                        Field('is_confidential'),
                        css_class='form-group col-md-6 mb-0'
                    ),
                    Column(
                        Field('is_active'),
                        css_class='form-group col-md-6 mb-0'
                    ),
                ),
                css_class='mt-3'
            ),
            Submit('submit', 'Upload Document', css_class='btn btn-primary mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        
        # Apply model validation
        try:
            # Create a temporary instance to validate business rules
            temp_instance = self.instance or DocpoolDocument()
            for field, value in cleaned_data.items():
                if hasattr(temp_instance, field):
                    setattr(temp_instance, field, value)
            
            # Set the user if provided
            if self.user and not temp_instance.uploaded_by:
                temp_instance.uploaded_by = self.user
                
            temp_instance.full_clean()
        except ValidationError as e:
            # Convert model validation errors to form errors
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        self.add_error(field, error)
            else:
                raise forms.ValidationError(str(e))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user and not instance.uploaded_by:
            instance.uploaded_by = self.user
        
        if commit:
            instance.save()
        return instance


class DocpoolSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search title, description, keywords...',
            'class': 'form-control'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=DocpoolDepartment.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    document_type = forms.ModelChoiceField(
        queryset=DocpoolDocumentType.objects.filter(is_active=True),
        required=False,
        empty_label="All Document Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    border = forms.ModelChoiceField(
        queryset=DocpoolDocumentBorder.objects.filter(is_active=True),
        required=False,
        empty_label="All Borders",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    month = forms.ChoiceField(
        required=False,
        choices=[('', 'All Months')] + [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    access_level = forms.ChoiceField(
        required=False,
        choices=[('', 'All Access Levels')] + DocpoolDocument._meta.get_field('access_level').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate year choices with available years
        from django.utils import timezone
        current_year = timezone.now().year
        years = list(range(current_year - 5, current_year + 2))
        year_choices = [('', 'All Years')] + [(year, str(year)) for year in years]
        self.fields['year'].choices = year_choices


class DocpoolAdvancedSearchForm(DocpoolSearchForm):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    file_type = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., pdf, docx, jpg',
            'class': 'form-control'
        })
    )
    
    has_reference = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_confidential = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Setup crispy forms layout
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-6 mb-0'),
                Column('file_type', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('department', css_class='form-group col-md-4 mb-0'),
                Column('document_type', css_class='form-group col-md-4 mb-0'),
                Column('border', css_class='form-group col-md-4 mb-0'),
            ),
            Row(
                Column('year', css_class='form-group col-md-3 mb-0'),
                Column('month', css_class='form-group col-md-3 mb-0'),
                Column('access_level', css_class='form-group col-md-3 mb-0'),
                Column('', css_class='form-group col-md-3 mb-0'),  # Spacer
            ),
            Row(
                Column('date_from', css_class='form-group col-md-6 mb-0'),
                Column('date_to', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column(
                    Field('has_reference', wrapper_class='form-check'),
                    css_class='form-group col-md-6 mb-0'
                ),
                Column(
                    Field('is_confidential', wrapper_class='form-check'),
                    css_class='form-group col-md-6 mb-0'
                ),
            ),
            Submit('submit', 'Advanced Search', css_class='btn btn-primary mt-3')
        )