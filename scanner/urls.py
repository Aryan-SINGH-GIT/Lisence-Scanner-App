from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('report/<uuid:upload_id>/', views.report, name='report'),
    path('license-info/', views.license_info, name='license_info'),
    
    # API endpoints
    path('api/status/<uuid:upload_id>/', views.upload_status, name='upload_status'),
    path('api/scan-status/<uuid:upload_id>/', views.api_scan_status, name='api_scan_status'),
    
    # Download endpoints
    path('download/<uuid:upload_id>/', views.download_report, name='download_report'),
]
