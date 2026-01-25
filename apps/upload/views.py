"""
Views for file upload operations.
"""
import os
import uuid
from PIL import Image
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import UploadedFile, FileUploadLog
from .serializers import UploadedFileSerializer


class UploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling file uploads.
    """
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only user's files."""
        user_uid = self.request.user.uid
        return UploadedFile.objects.filter(user_uid=user_uid)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def detect_file_type(self, mime_type):
        """Classify file type from MIME type."""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        return 'document'
    
    def get_image_dimensions(self, file_obj):
        """Get image dimensions."""
        try:
            file_obj.seek(0)
            with Image.open(file_obj) as img:
                return img.size
        except Exception:
            return None, None
        finally:
            file_obj.seek(0)
    
    def generate_thumbnail(self, file_obj, size=(400, 300)):
        """Generate thumbnail for image."""
        try:
            file_obj.seek(0)
            with Image.open(file_obj) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                output = BytesIO()
                img.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)
                
                return output
        except Exception:
            return None
        finally:
            file_obj.seek(0)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Handle file upload."""
        file_obj = request.FILES.get('file')
        listing_type = request.data.get('listing_type')
        listing_id = request.data.get('listing_id')
        is_primary = str(request.data.get('is_primary', 'false')).lower() == 'true'
        user_uid = request.user.uid
        
        # Validation
        if not all([file_obj, listing_type, listing_id]):
            return Response(
                {'error': 'Missing required fields: file, listing_type, listing_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get MIME type
        mime_type = file_obj.content_type or 'application/octet-stream'
        file_type = self.detect_file_type(mime_type)
        
        # Check file size limits
        max_size = settings.MAX_UPLOAD_SIZE.get(file_type, 5 * 1024 * 1024)
        if file_obj.size > max_size:
            return Response(
                {'error': f'File too large. Max size: {max_size // (1024*1024)}MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get image dimensions if applicable
        width, height = None, None
        if file_type == 'image':
            width, height = self.get_image_dimensions(file_obj)
        
        # Generate unique filename
        ext = os.path.splitext(file_obj.name)[1].lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_obj.name = unique_filename
        
        # Create database record
        uploaded_file = UploadedFile.objects.create(
            user_uid=user_uid,
            listing_type=listing_type,
            listing_id=listing_id,
            file_type=file_type,
            file=file_obj,
            file_size=file_obj.size,
            mime_type=mime_type,
            width=width,
            height=height,
            is_primary=is_primary,
        )
        
        # Generate thumbnail for images
        if file_type == 'image':
            thumb_data = self.generate_thumbnail(file_obj)
            if thumb_data:
                thumb_name = f"thumb_{uuid.uuid4()}.jpg"
                uploaded_file.thumbnail.save(thumb_name, ContentFile(thumb_data.read()), save=True)
        
        # Log the upload
        FileUploadLog.objects.create(
            user_uid=user_uid,
            action='upload',
            file_id=uploaded_file.id,
            file_name=file_obj.name,
            file_size=file_obj.size,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        serializer = self.get_serializer(uploaded_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def batch_upload(self, request):
        """Upload multiple files at once."""
        files = request.FILES.getlist('files')
        listing_type = request.data.get('listing_type')
        listing_id = request.data.get('listing_id')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        for index, file_obj in enumerate(files):
            try:
                # Create temporary request data
                request._request.FILES['file'] = file_obj
                request.data._mutable = True
                request.data['file'] = file_obj
                request.data['listing_type'] = listing_type
                request.data['listing_id'] = listing_id
                request.data['is_primary'] = str(index == 0).lower()
                request.data._mutable = False
                
                response = self.create(request)
                if response.status_code == 201:
                    results.append(response.data)
                else:
                    errors.append({
                        'file': file_obj.name,
                        'error': response.data.get('error', 'Unknown error')
                    })
            except Exception as e:
                errors.append({
                    'file': file_obj.name,
                    'error': str(e)
                })
        
        return Response({
            'success': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        })
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set a file as the primary image for its listing."""
        uploaded_file = self.get_object()
        
        # Unset all other primary images for this listing
        UploadedFile.objects.filter(
            listing_type=uploaded_file.listing_type,
            listing_id=uploaded_file.listing_id,
            user_uid=request.user.uid
        ).update(is_primary=False)
        
        # Set this one as primary
        uploaded_file.is_primary = True
        uploaded_file.save()
        
        return Response({'status': 'updated'})
    
    @action(detail=False, methods=['get'])
    def by_listing(self, request):
        """Get all files for a specific listing."""
        listing_type = request.query_params.get('listing_type')
        listing_id = request.query_params.get('listing_id')
        
        if not listing_type or not listing_id:
            return Response(
                {'error': 'Missing listing_type or listing_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        files = UploadedFile.objects.filter(
            listing_type=listing_type,
            listing_id=listing_id,
        ).order_by('-is_primary', '-uploaded_at')
        
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a file and log the action."""
        instance = self.get_object()
        
        # Log deletion
        FileUploadLog.objects.create(
            user_uid=request.user.uid,
            action='delete',
            file_id=instance.id,
            file_name=instance.file.name if instance.file else 'unknown',
            file_size=instance.file_size,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        return super().destroy(request, *args, **kwargs)
