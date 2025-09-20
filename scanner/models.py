from django.db import models
from django.core.validators import FileExtensionValidator
import os
import uuid


class Upload(models.Model):
    """
    Model to store information about uploaded files or directories.
    Each upload represents a single scanning session.
    """
    
    # Primary key using UUID for better security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # File information
    file = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['zip', 'tar', 'gz'])],
        help_text="Upload a zip file or compressed archive containing source code"
    )
    
    # Upload metadata
    original_filename = models.CharField(max_length=255, help_text="Original name of the uploaded file")
    file_size = models.BigIntegerField(help_text="Size of the uploaded file in bytes")
    upload_date = models.DateTimeField(auto_now_add=True, help_text="When the file was uploaded")
    
    # Processing status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Error handling
    error_message = models.TextField(blank=True, null=True, help_text="Error message if processing failed")
    
    # Processing metadata
    total_files_scanned = models.IntegerField(default=0, help_text="Total number of files scanned")
    processing_time = models.FloatField(null=True, blank=True, help_text="Time taken to process in seconds")
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
    
    def __str__(self):
        return f"{self.original_filename} - {self.status}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB for display purposes."""
        return round(self.file_size / (1024 * 1024), 2)


class LicenseReport(models.Model):
    """
    Model to store license detection results for individual files.
    Each record represents a single file and its detected license.
    """
    
    # Foreign key to the upload
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name='license_reports')
    
    # File information
    file_path = models.CharField(max_length=500, help_text="Relative path of the file within the archive")
    file_name = models.CharField(max_length=255, help_text="Name of the file")
    file_extension = models.CharField(max_length=10, blank=True, help_text="File extension")
    
    # License detection results
    detected_license = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Detected license type (e.g., MIT, Apache-2.0, GPL-3.0)"
    )
    license_confidence = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Confidence score for license detection (0.0 to 1.0)"
    )
    
    # File metadata
    file_size = models.BigIntegerField(help_text="Size of the file in bytes")
    line_count = models.IntegerField(null=True, blank=True, help_text="Number of lines in the file")
    
    # Detection metadata
    detection_method = models.CharField(
        max_length=50, 
        default='licensecheck',
        help_text="Method used to detect the license"
    )
    scan_date = models.DateTimeField(auto_now_add=True, help_text="When the file was scanned")
    
    # Additional information
    license_text = models.TextField(blank=True, help_text="Full text of the detected license")
    notes = models.TextField(blank=True, help_text="Additional notes about the license detection")
    
    class Meta:
        ordering = ['file_path']
        verbose_name = "License Report"
        verbose_name_plural = "License Reports"
        # Ensure unique file per upload
        unique_together = ['upload', 'file_path']
    
    def __str__(self):
        return f"{self.file_name} - {self.detected_license or 'Unknown'}"
    
    @property
    def file_size_kb(self):
        """Return file size in KB for display purposes."""
        return round(self.file_size / 1024, 2)
    
    @property
    def confidence_percentage(self):
        """Return confidence as percentage for display."""
        if self.license_confidence is not None:
            return round(self.license_confidence * 100, 1)
        return None


class LicenseType(models.Model):
    """
    Model to store information about different license types.
    This can be used for reference and validation.
    """
    
    name = models.CharField(max_length=100, unique=True, help_text="License name (e.g., MIT, Apache-2.0)")
    full_name = models.CharField(max_length=200, help_text="Full name of the license")
    description = models.TextField(help_text="Description of the license")
    is_osi_approved = models.BooleanField(default=False, help_text="Whether the license is OSI approved")
    is_fsf_approved = models.BooleanField(default=False, help_text="Whether the license is FSF approved")
    
    # License characteristics
    is_copyleft = models.BooleanField(default=False, help_text="Whether the license is copyleft")
    allows_commercial_use = models.BooleanField(default=True, help_text="Whether commercial use is allowed")
    requires_source_code = models.BooleanField(default=False, help_text="Whether source code must be provided")
    
    # Common identifiers
    spdx_identifier = models.CharField(max_length=50, blank=True, help_text="SPDX license identifier")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "License Type"
        verbose_name_plural = "License Types"
    
    def __str__(self):
        return self.name
