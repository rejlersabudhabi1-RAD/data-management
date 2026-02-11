"""
URL configuration for Versions app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentVersionViewSet, DatasetVersionViewSet, VersionComparisonViewSet

router = DefaultRouter()
router.register(r'documents', DocumentVersionViewSet, basename='document-version')
router.register(r'datasets', DatasetVersionViewSet, basename='dataset-version')
router.register(r'comparisons', VersionComparisonViewSet, basename='version-comparison')

urlpatterns = [
    path('', include(router.urls)),
]
