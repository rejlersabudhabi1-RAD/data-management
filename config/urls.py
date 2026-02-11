"""
URL Configuration for Data Management Service
Enterprise REST API endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for service monitoring
    Returns service status and version
    """
    return JsonResponse({
        'status': 'healthy',
        'service': settings.SERVICE_NAME,
        'version': settings.SERVICE_VERSION,
    })


def root_view(request):
    """
    API root endpoint with service information
    """
    return JsonResponse({
        'service': settings.SERVICE_NAME,
        'version': settings.SERVICE_VERSION,
        'endpoints': {
            'health': '/health/',
            'admin': '/admin/',
            'documents': '/api/documents/',
            'datasets': '/api/datasets/',
            'versions': '/api/versions/',
            'audit': '/api/audit/',
        },
        'documentation': '/api/docs/',
    })


urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # Root endpoint
    path('', root_view, name='api-root'),
    
    # API endpoints
    path('api/documents/', include('apps.documents.urls')),
    path('api/datasets/', include('apps.datasets.urls')),
    path('api/versions/', include('apps.versions.urls')),
    path('api/audit/', include('apps.audit.urls')),
]

# Configure admin site
admin.site.site_header = 'Data Management Service Admin'
admin.site.site_title = 'Data Management Admin'
admin.site.index_title = 'Welcome to Data Management Service'
