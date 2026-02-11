"""
URL configuration for Audit app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, SecurityEventViewSet, ApiUsageLogViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')
router.register(r'security', SecurityEventViewSet, basename='security-event')
router.register(r'usage', ApiUsageLogViewSet, basename='api-usage')

urlpatterns = [
    path('', include(router.urls)),
]
