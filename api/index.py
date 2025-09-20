import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use Vercel settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "license_scanner.settings_vercel")

application = get_wsgi_application()
