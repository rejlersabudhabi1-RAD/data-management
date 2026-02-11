"""
Views for Document management
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import Document, DocumentAccessLog
from .serializers import (
    DocumentSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    DocumentAccessLogSerializer,
)
from common.permissions import CanManageDocuments, IsAuthenticated

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document CRUD operations
    
    Endpoints:
    - GET /api/documents/ - List documents
    - POST /api/documents/ - Upload document
    - GET /api/documents/{id}/ - Get document details
    - PUT /api/documents/{id}/ - Update document metadata
    - DELETE /api/documents/{id}/ - Delete document
    - POST /api/documents/{id}/download/ - Download document
    - POST /api/documents/{id}/create_version/ - Create new version
    """
    
    queryset = Document.objects.filter(status='active')
    serializer_class = DocumentSerializer
    permission_classes = [CanManageDocuments]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'owner_service', 'status', 'created_by_user_id']
    search_fields = ['filename', 'metadata', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'filename', 'file_size']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'upload':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """
        Filter documents based on user permissions
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all documents
        if user.role in ['admin', 'superadmin']:
            return queryset
        
        # Regular users see only their documents or public documents
        return queryset.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        )
    
    def perform_create(self, serializer):
        """Create document with user context"""
        serializer.save()
        logger.info(f"Document created: {serializer.instance.id} by user {self.request.user.user_id}")
    
    def perform_update(self, serializer):
        """Update document"""
        serializer.save()
        logger.info(f"Document updated: {serializer.instance.id} by user {self.request.user.user_id}")
    
    def perform_destroy(self, instance):
        """Soft delete document"""
        instance.status = 'deleted'
        instance.is_latest = False
        instance.save(update_fields=['status', 'is_latest'])
        logger.info(f"Document deleted: {instance.id} by user {self.request.user.user_id}")
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """
        Download document and log access
        """
        document = self.get_object()
        
        # Log access
        self._log_document_access(document, 'download')
        
        # Return file URL
        return Response({
            'url': document.get_absolute_url(),
            'filename': document.filename,
            'mime_type': document.mime_type,
            'file_size': document.file_size,
        })
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """
        Create a new version of the document
        """
        document = self.get_object()
        
        # Import here to avoid circular dependency
        from apps.versions.models import DocumentVersion
        
        # Create version snapshot
        version = DocumentVersion.objects.create(
            document=document,
            version_number=document.current_version,
            file_path=document.file.name,
            file_size=document.file_size,
            checksum=document.checksum,
            metadata=document.metadata,
            created_by_user_id=request.user.user_id,
        )
        
        # Increment document version
        document.create_new_version()
        
        logger.info(f"Version created for document {document.id}: v{version.version_number}")
        
        return Response({
            'message': 'Version created successfully',
            'version_number': version.version_number,
            'document_id': str(document.id),
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_documents(self, request):
        """
        Get documents created by current user
        """
        documents = self.get_queryset().filter(
            created_by_user_id=request.user.user_id
        )
        
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def access_logs(self, request, pk=None):
        """
        Get access logs for a document
        Only admins or document owner can view
        """
        document = self.get_object()
        
        # Check permission
        if request.user.role not in ['admin', 'superadmin'] and document.created_by_user_id != request.user.user_id:
            return Response(
                {'error': 'You do not have permission to view access logs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = DocumentAccessLog.objects.filter(document=document)
        serializer = DocumentAccessLogSerializer(logs, many=True)
        
        return Response(serializer.data)
    
    def _log_document_access(self, document, access_type):
        """Log document access"""
        try:
            DocumentAccessLog.objects.create(
                document=document,
                user_id=self.request.user.user_id,
                access_type=access_type,
                ip_address=self._get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255],
            )
        except Exception as e:
            logger.error(f"Failed to log document access: {e}")
    
    def _get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


# Import Q for queryset filtering
from django.db import models
