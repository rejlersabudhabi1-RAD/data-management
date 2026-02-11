"""
URL configuration for Datasets app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatasetViewSet, DatasetTransformationViewSet

router = DefaultRouter()
router.register(r'', DatasetViewSet, basename='dataset')
router.register(r'transformations', DatasetTransformationViewSet, basename='transformation')

urlpatterns = [
    path('', include(router.urls)),
]
