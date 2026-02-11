"""
Views for Audit logs and security events
Read-only views for compliance and monitoring
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import AuditLog, SecurityEvent, ApiUsageLog
from .serializers import (
    AuditLogSerializer,
    AuditLogListSerializer,
    SecurityEventSerializer,
    SecurityEventListSerializer,
    ApiUsageLogSerializer,
)
from common.permissions import CanViewAuditLogs, IsAdmin

logger = logging.getLogger(__name__)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Audit logs
    Only admins and auditors can access
    
    Endpoints:
    - GET /api/audit/logs/ - List audit logs
    - GET /api/audit/logs/{id}/ - Get specific log
    - GET /api/audit/logs/statistics/ - Get audit statistics
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAuditLogs]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_id', 'action', 'entity_type', 'status']
    search_fields = ['entity_id', 'request_path', 'metadata']
    ordering_fields = ['timestamp', 'user_id']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get audit log statistics
        """
        # Time filters
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        last_30d = timezone.now() - timedelta(days=30)
        
        stats = {
            'total_events': self.queryset.count(),
            'last_24h': self.queryset.filter(timestamp__gte=last_24h).count(),
            'last_7d': self.queryset.filter(timestamp__gte=last_7d).count(),
            'last_30d': self.queryset.filter(timestamp__gte=last_30d).count(),
            
            'by_action': dict(
                self.queryset.values('action').annotate(count=Count('id')).values_list('action', 'count')
            ),
            
            'by_entity_type': dict(
                self.queryset.values('entity_type').annotate(count=Count('id')).values_list('entity_type', 'count')
            ),
            
            'by_status': dict(
                self.queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            
            'top_users': list(
                self.queryset.values('user_id')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Get audit logs for specific user
        """
        logs = self.queryset.filter(user_id=user_id)
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='entity/(?P<entity_type>[^/.]+)/(?P<entity_id>[^/.]+)')
    def by_entity(self, request, entity_type=None, entity_id=None):
        """
        Get audit logs for specific entity
        """
        logs = self.queryset.filter(entity_type=entity_type, entity_id=entity_id)
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class SecurityEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Security events
    Admins can view and resolve security events
    
    Endpoints:
    - GET /api/audit/security/ - List security events
    - GET /api/audit/security/{id}/ - Get specific event
    - PUT /api/audit/security/{id}/ - Resolve security event
    - GET /api/audit/security/unresolved/ - Get unresolved events
    """
    
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'resolved', 'user_id']
    ordering_fields = ['timestamp', 'severity']
    ordering = ['-timestamp']
    
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'list':
            return SecurityEventListSerializer
        return SecurityEventSerializer
    
    def update(self, request, *args, **kwargs):
        """Only allow updating resolution fields"""
        instance = self.get_object()
        
        # Add resolved_by and resolved_at
        data = request.data.copy()
        if data.get('resolved'):
            data['resolved_by'] = request.user.user_id
            data['resolved_at'] = timezone.now()
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """
        Get unresolved security events
        """
        events = self.queryset.filter(resolved=False)
        
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """
        Get critical security events
        """
        events = self.queryset.filter(severity='CRITICAL')
        
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get security event statistics
        """
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_events': self.queryset.count(),
            'unresolved': self.queryset.filter(resolved=False).count(),
            'critical_unresolved': self.queryset.filter(
                severity='CRITICAL',
                resolved=False
            ).count(),
            
            'last_24h': self.queryset.filter(timestamp__gte=last_24h).count(),
            'last_7d': self.queryset.filter(timestamp__gte=last_7d).count(),
            
            'by_severity': dict(
                self.queryset.values('severity')
                .annotate(count=Count('id'))
                .values_list('severity', 'count')
            ),
            
            'by_event_type': dict(
                self.queryset.values('event_type')
                .annotate(count=Count('id'))
                .values_list('event_type', 'count')
            ),
        }
        
        return Response(stats)


class ApiUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for API usage logs
    For monitoring and analytics
    """
    
    queryset = ApiUsageLog.objects.all()
    serializer_class = ApiUsageLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user_id', 'endpoint', 'method', 'status_code']
    ordering_fields = ['timestamp', 'response_time_ms']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get API usage statistics
        """
        last_24h = timezone.now() - timedelta(hours=24)
        
        stats = {
            'total_requests': self.queryset.count(),
            'last_24h': self.queryset.filter(timestamp__gte=last_24h).count(),
            
            'avg_response_time': self.queryset.aggregate(
                avg=Count('response_time_ms')
            )['avg'],
            
            'top_endpoints': list(
                self.queryset.values('endpoint', 'method')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            
            'top_users': list(
                self.queryset.values('user_id')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            
            'status_codes': dict(
                self.queryset.values('status_code')
                .annotate(count=Count('id'))
                .values_list('status_code', 'count')
            ),
        }
        
        return Response(stats)
