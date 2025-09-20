# Update views.py to use SimpleLicenseScanner for Vercel
# This is a patch to make the app work in serverless environment

import os
import sys
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
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

# Import the simple scanner for Vercel compatibility
try:
    from .simple_scanner import SimpleLicenseScanner
    LicenseScanner = SimpleLicenseScanner
except ImportError:
    from .utils import LicenseScanner

# Rest of the views remain the same...
