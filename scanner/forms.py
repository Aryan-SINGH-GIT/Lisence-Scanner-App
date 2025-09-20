from django import forms
from django.core.exceptions import ValidationError
from .models import Upload
import os


class FileUploadForm(forms.ModelForm):
    """
    Form for uploading files to be scanned for licenses.
    Handles validation and file type checking.
    """
    
    class Meta:
        model = Upload
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.zip,.tar,.gz,.tar.gz',
                'id': 'file-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom attributes and validation
        self.fields['file'].required = True
        self.fields['file'].help_text = "Upload a zip file or compressed archive containing source code"
    
    def clean_file(self):
        """
        Validate the uploaded file.
        Check file size, type, and other constraints.
        """
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Please select a file to upload.")
        
        # Check file size (limit to 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if file.size > max_size:
            raise ValidationError(
                f"File size too large. Maximum allowed size is {max_size // (1024*1024)}MB. "
                f"Your file is {file.size // (1024*1024)}MB."
            )
        
        # Check file extension
        allowed_extensions = ['.zip', '.tar', '.gz', '.tar.gz']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        # Handle .tar.gz files
        if file.name.lower().endswith('.tar.gz'):
            file_extension = '.tar.gz'
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Invalid file type. Allowed types are: {', '.join(allowed_extensions)}"
            )
        
        return file
    
    def save(self, commit=True):
        """
        Save the form and set additional fields.
        """
        instance = super().save(commit=False)
        
        # Set original filename and file size
        instance.original_filename = self.cleaned_data['file'].name
        instance.file_size = self.cleaned_data['file'].size
        
        if commit:
            instance.save()
        
        return instance


class ScanOptionsForm(forms.Form):
    """
    Form for additional scan options and settings.
    """
    
    # Scan options
    scan_recursively = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Scan all subdirectories recursively",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_binary_files = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Include binary files in the scan (may slow down processing)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # File type filters
    INCLUDE_FILE_TYPES = [
        ('all', 'All Files'),
        ('code', 'Code Files Only'),
        ('license', 'License Files Only'),
        ('custom', 'Custom Extensions'),
    ]
    
    include_file_types = forms.ChoiceField(
        choices=INCLUDE_FILE_TYPES,
        initial='code',
        help_text="Select which file types to include in the scan",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    custom_extensions = forms.CharField(
        required=False,
        max_length=200,
        help_text="Comma-separated list of file extensions (e.g., .py,.js,.java)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '.py, .js, .java, .cpp'
        })
    )
    
    # License detection options
    confidence_threshold = forms.FloatField(
        required=False,
        initial=0.7,
        min_value=0.0,
        max_value=1.0,
        help_text="Minimum confidence threshold for license detection (0.0 to 1.0)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0.0',
            'max': '1.0'
        })
    )
    
    def clean_custom_extensions(self):
        """
        Validate and clean custom extensions input.
        """
        extensions = self.cleaned_data.get('custom_extensions', '')
        include_type = self.cleaned_data.get('include_file_types', 'all')
        
        if include_type == 'custom' and not extensions:
            raise ValidationError("Please specify custom file extensions.")
        
        if extensions:
            # Clean and validate extensions
            ext_list = [ext.strip().lower() for ext in extensions.split(',')]
            ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
            
            # Remove duplicates and empty strings
            ext_list = list(set([ext for ext in ext_list if ext != '.']))
            
            if not ext_list:
                raise ValidationError("No valid extensions found.")
            
            return ','.join(ext_list)
        
        return extensions


class ReportFilterForm(forms.Form):
    """
    Form for filtering license reports.
    """
    
    # License filter
    license_filter = forms.CharField(
        required=False,
        max_length=100,
        help_text="Filter by license type",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., MIT, Apache, GPL'
        })
    )
    
    # File type filter
    file_extension_filter = forms.CharField(
        required=False,
        max_length=50,
        help_text="Filter by file extension",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., .py, .js, .java'
        })
    )
    
    # Confidence filter
    min_confidence = forms.FloatField(
        required=False,
        min_value=0.0,
        max_value=1.0,
        help_text="Minimum confidence threshold",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0.0',
            'max': '1.0',
            'placeholder': '0.0'
        })
    )
    
    # Sort options
    SORT_CHOICES = [
        ('file_path', 'File Path'),
        ('detected_license', 'License Type'),
        ('license_confidence', 'Confidence'),
        ('file_size', 'File Size'),
        ('scan_date', 'Scan Date'),
    ]
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        initial='file_path',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_order = forms.ChoiceField(
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        initial='asc',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
