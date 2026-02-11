"""
Admin configuration for Versions app
"""

from django.contrib import admin
from .models import DocumentVersion, DatasetVersion, VersionComparison


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'document', 'version_number',
        'file_size', 'checksum',
        'created_by_user_id', 'created_at',
    ]
    list_filter = ['created_at', 'version_number']
    search_fields = ['document__filename', 'document__id', 'created_by_user_id']
    readonly_fields = [
        'id', 'document', 'version_number',
        'file_path', 'file_size', 'checksum',
        'metadata', 'tags',
        'created_by_user_id', 'created_at', 'change_notes',
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification - versions are immutable"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - versions are immutable"""
        return False


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'dataset', 'version_number',
        'row_count', 'column_count',
        'created_by_user_id', 'created_at',
    ]
    list_filter = ['created_at', 'version_number']
    search_fields = ['dataset__name', 'dataset__id', 'created_by_user_id']
    readonly_fields = [
        'id', 'dataset', 'version_number',
        'data_snapshot', 'schema_snapshot',
        'row_count', 'column_count', 'checksum',
        'metadata', 'tags',
        'created_by_user_id', 'created_at', 'change_notes',
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification - versions are immutable"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - versions are immutable"""
        return False


@admin.register(VersionComparison)
class VersionComparisonAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'entity_type', 'entity_id',
        'version_from', 'version_to',
        'compared_by_user_id', 'compared_at',
    ]
    list_filter = ['entity_type', 'compared_at']
    search_fields = ['entity_id', 'compared_by_user_id']
    readonly_fields = ['id', 'compared_at']
