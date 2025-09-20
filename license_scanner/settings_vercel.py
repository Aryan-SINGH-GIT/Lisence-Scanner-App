"""
Production settings for Vercel deployment
"""
import os
from .settings import *

# Security settings for production
DEBUG = False
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Allowed hosts for Vercel
ALLOWED_HOSTS = [
    ".vercel.app",
    ".now.sh",
    "localhost",
    "127.0.0.1"
]

# Database configuration for Vercel (PostgreSQL recommended)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "license_scanner"),
        "USER": os.environ.get("DATABASE_USER", "postgres"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

# Static files configuration for Vercel
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files - for Vercel, you might want to use cloud storage
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# File upload settings (reduced for Vercel limits)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB (Vercel limit)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Disable Scancode for Vercel (not compatible with serverless)
SCANCODE_BIN = None

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
    },
}
