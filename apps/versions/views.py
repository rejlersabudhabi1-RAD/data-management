"""
Views for Version management
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import models
import logging

from .models import DocumentVersion, DatasetVersion, VersionComparison
from .serializers import (
    DocumentVersionSerializer,
    DatasetVersionSerializer,
    DatasetVersionListSerializer,
    VersionComparisonSerializer,
)
from apps.documents.models import Document
from apps.datasets.models import Dataset
from common.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Document versions
    Versions are immutable and created automatically
    
    Endpoints:
    - GET /api/versions/documents/ - List document versions
    - GET /api/versions/documents/{id}/ - Get specific version
    """
    
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'version_number', 'created_by_user_id']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
    
    def get_queryset(self):
        """Filter versions based on document access"""
        user = self.request.user
        
        # Admins see all versions
        if user.role in ['admin', 'superadmin']:
            return self.queryset
        
        # Get accessible documents
        accessible_docs = Document.objects.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        )
        
        return self.queryset.filter(document__in=accessible_docs)
    
    @action(detail=False, methods=['get'], url_path='document/(?P<document_id>[^/.]+)')
    def by_document(self, request, document_id=None):
        """
        Get all versions for a specific document
        """
        versions = self.get_queryset().filter(document_id=document_id)
        
        page = self.paginate_queryset(versions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)


class DatasetVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Dataset versions
    Versions are immutable and created automatically
    
    Endpoints:
    - GET /api/versions/datasets/ - List dataset versions
    - GET /api/versions/datasets/{id}/ - Get specific version
    """
    
    queryset = DatasetVersion.objects.all()
    serializer_class = DatasetVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['dataset', 'version_number', 'created_by_user_id']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'list':
            return DatasetVersionListSerializer
        return DatasetVersionSerializer
    
    def get_queryset(self):
        """Filter versions based on dataset access"""
        user = self.request.user
        
        # Admins see all versions
        if user.role in ['admin', 'superadmin']:
            return self.queryset
        
        # Get accessible datasets
        accessible_datasets = Dataset.objects.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        )
        
        return self.queryset.filter(dataset__in=accessible_datasets)
    
    @action(detail=False, methods=['get'], url_path='dataset/(?P<dataset_id>[^/.]+)')
    def by_dataset(self, request, dataset_id=None):
        """
        Get all versions for a specific dataset
        """
        versions = self.get_queryset().filter(dataset_id=dataset_id)
        
        page = self.paginate_queryset(versions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)


class VersionComparisonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for version comparisons
    """
    queryset = VersionComparison.objects.all()
    serializer_class = VersionComparisonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'entity_id']
    ordering_fields = ['compared_at']
    ordering = ['-compared_at']
    
    def get_queryset(self):
        """Filter comparisons based on access"""
        user = self.request.user
        
        if user.role in ['admin', 'superadmin']:
            return self.queryset
        
        # Filter based on accessible documents and datasets
        accessible_docs = Document.objects.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        ).values_list('id', flat=True)
        
        accessible_datasets = Dataset.objects.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        ).values_list('id', flat=True)
        
        return self.queryset.filter(
            models.Q(entity_type='document', entity_id__in=accessible_docs) |
            models.Q(entity_type='dataset', entity_id__in=accessible_datasets)
        )
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        Compare two versions of a document or dataset
        """
        entity_type = request.data.get('entity_type')
        entity_id = request.data.get('entity_id')
        version_from = request.data.get('version_from')
        version_to = request.data.get('version_to')
        
        if not all([entity_type, entity_id, version_from, version_to]):
            return Response(
                {'error': 'Missing required fields: entity_type, entity_id, version_from, version_to'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if entity_type == 'document':
                changes = self._compare_documents(entity_id, version_from, version_to)
            elif entity_type == 'dataset':
                changes = self._compare_datasets(entity_id, version_from, version_to)
            else:
                return Response(
                    {'error': 'Invalid entity_type. Must be "document" or "dataset"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create comparison record
            comparison = VersionComparison.objects.create(
                entity_type=entity_type,
                entity_id=entity_id,
                version_from=version_from,
                version_to=version_to,
                changes=changes,
                summary=self._generate_summary(changes),
                compared_by_user_id=request.user.user_id,
            )
            
            serializer = VersionComparisonSerializer(comparison)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Version comparison failed: {str(e)}")
            return Response(
                {'error': f'Comparison failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _compare_documents(self, document_id, version_from, version_to):
        """Compare two document versions"""
        v_from = DocumentVersion.objects.get(document_id=document_id, version_number=version_from)
        v_to = DocumentVersion.objects.get(document_id=document_id, version_number=version_to)
        
        changes = {
            'file_size_change': v_to.file_size - v_from.file_size,
            'checksum_changed': v_from.checksum != v_to.checksum,
            'metadata_changes': self._diff_json(v_from.metadata, v_to.metadata),
            'tags_added': list(set(v_to.tags) - set(v_from.tags)),
            'tags_removed': list(set(v_from.tags) - set(v_to.tags)),
        }
        
        return changes
    
    def _compare_datasets(self, dataset_id, version_from, version_to):
        """Compare two dataset versions"""
        v_from = DatasetVersion.objects.get(dataset_id=dataset_id, version_number=version_from)
        v_to = DatasetVersion.objects.get(dataset_id=dataset_id, version_number=version_to)
        
        changes = {
            'row_count_change': (v_to.row_count or 0) - (v_from.row_count or 0),
            'column_count_change': (v_to.column_count or 0) - (v_from.column_count or 0),
            'checksum_changed': v_from.checksum != v_to.checksum,
            'schema_changed': v_from.schema_snapshot != v_to.schema_snapshot,
            'metadata_changes': self._diff_json(v_from.metadata, v_to.metadata),
        }
        
        return changes
    
    def _diff_json(self, obj1, obj2):
        """Simple JSON diff"""
        changes = {}
        all_keys = set(obj1.keys()) | set(obj2.keys())
        
        for key in all_keys:
            if key not in obj1:
                changes[key] = {'added': obj2[key]}
            elif key not in obj2:
                changes[key] = {'removed': obj1[key]}
            elif obj1[key] != obj2[key]:
                changes[key] = {'from': obj1[key], 'to': obj2[key]}
        
        return changes
    
    def _generate_summary(self, changes):
        """Generate human-readable summary"""
        summary_parts = []
        
        for key, value in changes.items():
            if isinstance(value, dict):
                summary_parts.append(f"{key}: {len(value)} changes")
            elif isinstance(value, (list, tuple)):
                summary_parts.append(f"{key}: {len(value)} items")
            else:
                summary_parts.append(f"{key}: {value}")
        
        return ', '.join(summary_parts)
