"""
Views for Dataset management
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
import logging

from .models import Dataset, DatasetTransformation
from .serializers import (
    DatasetSerializer,
    DatasetListSerializer,
    DatasetCreateSerializer,
    DatasetTransformationSerializer,
)
from common.permissions import CanManageDatasets, IsAuthenticated

logger = logging.getLogger(__name__)


class DatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dataset CRUD operations
    
    Endpoints:
    - GET /api/datasets/ - List datasets
    - POST /api/datasets/ - Create dataset
    - GET /api/datasets/{id}/ - Get dataset details
    - PUT /api/datasets/{id}/ - Update dataset
    - DELETE /api/datasets/{id}/ - Delete dataset
    - POST /api/datasets/{id}/create_version/ - Create new version
    - GET /api/datasets/{id}/versions/ - Get all versions
    - GET /api/datasets/{id}/validate/ - Validate dataset against schema
    """
    
    queryset = Dataset.objects.filter(status='active')
    serializer_class = DatasetSerializer
    permission_classes = [CanManageDatasets]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dataset_type', 'domain', 'format', 'status', 'created_by_user_id']
    search_fields = ['name', 'description', 'tags', 'metadata']
    ordering_fields = ['created_at', 'updated_at', 'name', 'version']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DatasetListSerializer
        elif self.action == 'create':
            return DatasetCreateSerializer
        return DatasetSerializer
    
    def get_queryset(self):
        """Filter datasets based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all datasets
        if user.role in ['admin', 'superadmin']:
            return queryset
        
        # Regular users see only their datasets or public datasets
        return queryset.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        )
    
    def perform_create(self, serializer):
        """Create dataset"""
        serializer.save()
        logger.info(f"Dataset created: {serializer.instance.id} by user {self.request.user.user_id}")
    
    def perform_update(self, serializer):
        """Update dataset"""
        serializer.save()
        logger.info(f"Dataset updated: {serializer.instance.id} by user {self.request.user.user_id}")
    
    def perform_destroy(self, instance):
        """Soft delete dataset"""
        instance.status = 'deleted'
        instance.is_latest = False
        instance.save(update_fields=['status', 'is_latest'])
        logger.info(f"Dataset deleted: {instance.id} by user {self.request.user.user_id}")
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """
        Create a new version of the dataset
        """
        dataset = self.get_object()
        
        # Get new data from request
        new_data = request.data.get('data')
        if not new_data:
            return Response(
                {'error': 'Data field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create new version
            new_dataset = dataset.create_version(new_data, request.user.user_id)
            
            logger.info(f"Version created for dataset {dataset.id}: v{new_dataset.version}")
            
            serializer = DatasetSerializer(new_dataset)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to create version: {str(e)}")
            return Response(
                {'error': f'Failed to create version: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions of a dataset
        """
        dataset = self.get_object()
        
        # Get all versions (including this one and its children)
        if dataset.parent_dataset:
            # If this is a version, get all versions from parent
            versions = Dataset.objects.filter(
                models.Q(id=dataset.parent_dataset.id) |
                models.Q(parent_dataset=dataset.parent_dataset)
            ).order_by('version')
        else:
            # If this is the original, get all versions
            versions = Dataset.objects.filter(
                models.Q(id=dataset.id) |
                models.Q(parent_dataset=dataset)
            ).order_by('version')
        
        serializer = DatasetListSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def validate(self, request, pk=None):
        """
        Validate dataset against its schema
        """
        dataset = self.get_object()
        
        if not dataset.schema:
            return Response({
                'valid': True,
                'message': 'No schema defined for validation'
            })
        
        try:
            dataset.validate_schema()
            return Response({
                'valid': True,
                'message': 'Dataset is valid according to schema'
            })
        except ValueError as e:
            return Response({
                'valid': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_datasets(self, request):
        """
        Get datasets created by current user
        """
        datasets = self.get_queryset().filter(
            created_by_user_id=request.user.user_id
        )
        
        page = self.paginate_queryset(datasets)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(datasets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get detailed statistics for a dataset
        """
        dataset = self.get_object()
        
        stats = {
            'id': str(dataset.id),
            'name': dataset.name,
            'row_count': dataset.row_count,
            'column_count': dataset.column_count,
            'version': dataset.version,
            'format': dataset.format,
            'domain': dataset.domain,
            'dataset_type': dataset.dataset_type,
            'size_bytes': len(str(dataset.data).encode('utf-8')),
            'checksum': dataset.checksum,
            'has_schema': bool(dataset.schema),
            'created_at': dataset.created_at,
            'updated_at': dataset.updated_at,
        }
        
        # Add data structure info
        if isinstance(dataset.data, list):
            stats['structure'] = 'array'
            if dataset.data and isinstance(dataset.data[0], dict):
                stats['fields'] = list(dataset.data[0].keys())
        elif isinstance(dataset.data, dict):
            stats['structure'] = 'object'
            stats['fields'] = list(dataset.data.keys())
        
        return Response(stats)


class DatasetTransformationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dataset Transformations
    """
    queryset = DatasetTransformation.objects.all()
    serializer_class = DatasetTransformationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['source_dataset', 'target_dataset', 'transformation_type']
    ordering_fields = ['performed_at']
    ordering = ['-performed_at']
    
    def get_queryset(self):
        """Filter transformations user has access to"""
        user = self.request.user
        
        if user.role in ['admin', 'superadmin']:
            return self.queryset
        
        # Get datasets user has access to
        accessible_datasets = Dataset.objects.filter(
            models.Q(created_by_user_id=user.user_id) |
            models.Q(is_public=True) |
            models.Q(allowed_roles__contains=[user.role])
        )
        
        # Filter transformations
        return self.queryset.filter(
            models.Q(source_dataset__in=accessible_datasets) |
            models.Q(target_dataset__in=accessible_datasets)
        )
