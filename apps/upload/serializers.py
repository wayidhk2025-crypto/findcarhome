"""
Serializers for the upload app.
"""
from rest_framework import serializers
from .models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for UploadedFile model."""
    
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = [
            'id',
            'user_uid',
            'listing_type',
            'listing_id',
            'file_type',
            'file',
            'url',
            'thumbnail_url',
            'is_primary',
            'file_size',
            'mime_type',
            'width',
            'height',
            'uploaded_at',
        ]
        read_only_fields = [
            'id',
            'user_uid',
            'file_type',
            'url',
            'thumbnail_url',
            'file_size',
            'mime_type',
            'width',
            'height',
            'uploaded_at',
        ]
    
    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.url
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return obj.thumbnail_url


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload requests."""
    
    file = serializers.FileField()
    listing_type = serializers.ChoiceField(choices=['house', 'car'])
    listing_id = serializers.CharField(max_length=128)
    is_primary = serializers.BooleanField(default=False)
