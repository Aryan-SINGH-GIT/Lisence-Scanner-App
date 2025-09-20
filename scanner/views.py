from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import zipfile
import tarfile
import tempfile
import shutil
import time
import threading
from pathlib import Path
import mimetypes
import chardet

from .models import Upload, LicenseReport, LicenseType
from .forms import FileUploadForm, ScanOptionsForm, ReportFilterForm
from .utils import LicenseScanner


def home(request):
    """
    Home page view - displays the upload form.
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save the upload
                upload = form.save()
                
                # Start license scanning in background
                start_license_scanning(upload.id)
                
                messages.success(
                    request, 
                    f"File '{upload.original_filename}' uploaded successfully! "
                    f"Scanning started. You will be redirected to the report page."
                )
                
                return redirect('report', upload_id=upload.id)
                
            except Exception as e:
                messages.error(request, f"Error uploading file: {str(e)}")
                form = FileUploadForm()
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FileUploadForm()
    
    # Get recent uploads for display
    recent_uploads = Upload.objects.all()[:5]
    
    context = {
        'form': form,
        'recent_uploads': recent_uploads,
    }
    
    return render(request, 'scanner/upload.html', context)


def report(request, upload_id):
    """
    Report page view - displays license scan results.
    """
    upload = get_object_or_404(Upload, id=upload_id)
    
    # Get filter form
    filter_form = ReportFilterForm(request.GET)
    
    # Get license reports for this upload
    reports = LicenseReport.objects.filter(upload=upload)
    
    # Apply filters
    if filter_form.is_valid():
        license_filter = filter_form.cleaned_data.get('license_filter')
        file_extension_filter = filter_form.cleaned_data.get('file_extension_filter')
        min_confidence = filter_form.cleaned_data.get('min_confidence')
        sort_by = filter_form.cleaned_data.get('sort_by', 'file_path')
        sort_order = filter_form.cleaned_data.get('sort_order', 'asc')
        
        # Apply license filter
        if license_filter:
            reports = reports.filter(
                Q(detected_license__icontains=license_filter) |
                Q(license_text__icontains=license_filter)
            )
        
        # Apply file extension filter
        if file_extension_filter:
            if not file_extension_filter.startswith('.'):
                file_extension_filter = f'.{file_extension_filter}'
            reports = reports.filter(file_extension__iexact=file_extension_filter)
        
        # Apply confidence filter
        if min_confidence is not None:
            reports = reports.filter(license_confidence__gte=min_confidence)
        
        # Apply sorting
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        reports = reports.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(reports, 50)  # Show 50 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_files = reports.count()
    unique_licenses = reports.values('detected_license').distinct().count()
    high_confidence = reports.filter(license_confidence__gte=0.8).count()
    unknown_licenses = reports.filter(detected_license='').count()
    
    # License distribution
    license_distribution = reports.values('detected_license').annotate(
        count=Count('detected_license')
    ).order_by('-count')[:10]
    
    context = {
        'upload': upload,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_files': total_files,
        'unique_licenses': unique_licenses,
        'high_confidence': high_confidence,
        'unknown_licenses': unknown_licenses,
        'license_distribution': license_distribution,
    }
    
    return render(request, 'scanner/report.html', context)


def upload_status(request, upload_id):
    """
    AJAX endpoint to check upload processing status.
    """
    upload = get_object_or_404(Upload, id=upload_id)
    
    return JsonResponse({
        'status': upload.status,
        'total_files_scanned': upload.total_files_scanned,
        'processing_time': upload.processing_time,
        'error_message': upload.error_message,
    })


def download_report(request, upload_id):
    """
    Download license report as CSV file.
    """
    upload = get_object_or_404(Upload, id=upload_id)
    reports = LicenseReport.objects.filter(upload=upload)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="license_report_{upload_id}.csv"'
    
    # Write CSV header
    response.write('File Path,File Name,License,Confidence,File Size (KB),Line Count,Detection Method\n')
    
    # Write CSV data
    for report in reports:
        confidence = report.license_confidence or 0
        file_size_kb = report.file_size_kb
        line_count = report.line_count or 0
        
        response.write(
            f'"{report.file_path}",'
            f'"{report.file_name}",'
            f'"{report.detected_license}",'
            f'{confidence},'
            f'{file_size_kb},'
            f'{line_count},'
            f'"{report.detection_method}"\n'
        )
    
    return response


def start_license_scanning(upload_id):
    """
    Start license scanning in a background thread.
    """
    def scan_worker():
        try:
            upload = Upload.objects.get(id=upload_id)
            upload.status = 'processing'
            upload.save()
            
            start_time = time.time()
            
            # Initialize scanner
            scanner = LicenseScanner()
            
            # Extract and scan files
            extracted_path = extract_uploaded_file(upload)
            if extracted_path:
                # Scan for licenses
                results = scanner.scan_directory(extracted_path)
                
                # Save results to database
                save_scan_results(upload, results)
                
                # Clean up extracted files
                shutil.rmtree(extracted_path, ignore_errors=True)
            
            # Update upload status
            end_time = time.time()
            upload.status = 'completed'
            upload.processing_time = end_time - start_time
            upload.save()
            
        except Exception as e:
            # Update upload status with error
            upload = Upload.objects.get(id=upload_id)
            upload.status = 'failed'
            upload.error_message = str(e)
            upload.save()
    
    # Start background thread
    thread = threading.Thread(target=scan_worker)
    thread.daemon = True
    thread.start()


def extract_uploaded_file(upload):
    """
    Extract uploaded archive file to temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        file_path = upload.file.path
        
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        
        elif file_path.endswith(('.tar', '.tar.gz', '.tgz')):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(temp_dir)
        
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
        
        return temp_dir
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


def save_scan_results(upload, results):
    """
    Save license scan results to database.
    """
    total_files = 0
    
    for file_path, result in results.items():
        try:
            # Get file information
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1]
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Count lines in file
            line_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
            except:
                pass
            
            # Create license report
            LicenseReport.objects.create(
                upload=upload,
                file_path=file_path,
                file_name=file_name,
                file_extension=file_extension,
                detected_license=result.get('license', ''),
                license_confidence=result.get('confidence', 0.0),
                file_size=file_size,
                line_count=line_count,
                detection_method=result.get('method', 'licensecheck'),
                license_text=result.get('license_text', ''),
                notes=result.get('notes', '')
            )
            
            total_files += 1
            
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing file {file_path}: {e}")
            continue
    
    # Update upload with total files scanned
    upload.total_files_scanned = total_files
    upload.save()


def license_info(request):
    """
    Display information about different license types.
    """
    licenses = LicenseType.objects.all()
    
    context = {
        'licenses': licenses,
    }
    
    return render(request, 'scanner/license_info.html', context)


def api_scan_status(request, upload_id):
    """
    API endpoint for checking scan status.
    """
    try:
        upload = Upload.objects.get(id=upload_id)
        return JsonResponse({
            'status': upload.status,
            'total_files_scanned': upload.total_files_scanned,
            'processing_time': upload.processing_time,
            'error_message': upload.error_message,
        })
    except Upload.DoesNotExist:
        return JsonResponse({'error': 'Upload not found'}, status=404)
