"""
Upload app models for file storage metadata.
"""
from django.db import models


class UploadedFile(models.Model):
    """Model for tracking uploaded files."""
    
    FILE_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    )
    
    LISTING_TYPES = (
        ('house', 'House'),
        ('car', 'Car'),
    )
    
    user_uid = models.CharField(max_length=128, db_index=True)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES)
    listing_id = models.CharField(max_length=128, db_index=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='image')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, default='')
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['listing_type', 'listing_id']),
            models.Index(fields=['user_uid', 'uploaded_at']),
        ]
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.listing_type}/{self.listing_id} - {self.file.name}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete physical files
        if self.file:
            self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)
    
    @property
    def url(self):
        return self.file.url if self.file else None
    
    @property
    def thumbnail_url(self):
        return self.thumbnail.url if self.thumbnail else None


class FileUploadLog(models.Model):
    """Log for tracking upload activities."""
    
    user_uid = models.CharField(max_length=128)
    action = models.CharField(max_length=20)  # upload, delete, update
    file_id = models.IntegerField(null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.file_name} by {self.user_uid}"
