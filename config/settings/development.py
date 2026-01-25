"""
Development settings for FindCarHome backend.
"""
from .base import *

DEBUG = True

# Use local file storage for development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
