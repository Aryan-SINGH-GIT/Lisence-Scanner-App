from django.contrib import admin
from .models import Upload, LicenseReport, LicenseType

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "file_size", "status", "total_files_scanned", "upload_date")
    list_filter = ("status", "upload_date")
    search_fields = ("original_filename", "id")

@admin.register(LicenseReport)
class LicenseReportAdmin(admin.ModelAdmin):
    list_display = ("upload", "file_path", "detected_license", "license_confidence", "file_size", "scan_date")
    list_filter = ("detected_license", "detection_method", "scan_date")
    search_fields = ("file_path", "file_name", "detected_license")

@admin.register(LicenseType)
class LicenseTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "spdx_identifier", "is_osi_approved", "is_fsf_approved")
    search_fields = ("name", "spdx_identifier")
