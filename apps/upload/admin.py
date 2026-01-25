from django.contrib import admin
from .models import UploadedFile, FileUploadLog


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing_type', 'listing_id', 'file_type', 'is_primary', 'uploaded_at']
    list_filter = ['listing_type', 'file_type', 'is_primary']
    search_fields = ['user_uid', 'listing_id']
    readonly_fields = ['uploaded_at', 'file_size', 'mime_type', 'width', 'height']


@admin.register(FileUploadLog)
class FileUploadLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_uid', 'action', 'file_name', 'timestamp']
    list_filter = ['action']
    search_fields = ['user_uid', 'file_name']
    readonly_fields = ['timestamp']
