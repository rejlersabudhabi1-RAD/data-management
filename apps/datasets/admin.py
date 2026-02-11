"""
Admin configuration for Datasets app
"""

from django.contrib import admin
from .models import Dataset, DatasetTransformation


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'dataset_type', 'domain', 'format',
        'version', 'is_latest', 'row_count', 'status',
        'created_by_user_id', 'created_at',
    ]
    list_filter = ['dataset_type', 'domain', 'format', 'status', 'is_latest', 'created_at']
    search_fields = ['name', 'description', 'id', 'created_by_user_id']
    readonly_fields = [
        'id', 'checksum', 'file_size', 'version', 'parent_dataset',
        'row_count', 'column_count', 'created_at', 'updated_at',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'status')
        }),
        ('Classification', {
            'fields': ('dataset_type', 'domain', 'source_service', 'format')
        }),
        ('Data', {
            'fields': ('data', 'schema', 'file', 'file_size', 'checksum')
        }),
        ('Versioning', {
            'fields': ('version', 'parent_dataset', 'is_latest')
        }),
        ('Statistics', {
            'fields': ('row_count', 'column_count')
        }),
        ('Metadata', {
            'fields': ('metadata', 'tags')
        }),
        ('Access Control', {
            'fields': ('created_by_user_id', 'created_by_role', 'is_public', 'allowed_roles')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent hard delete from admin"""
        return False


@admin.register(DatasetTransformation)
class DatasetTransformationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'source_dataset', 'target_dataset',
        'transformation_type', 'performed_by_user_id', 'performed_at',
    ]
    list_filter = ['transformation_type', 'performed_at']
    search_fields = ['source_dataset__name', 'target_dataset__name', 'performed_by_user_id']
    readonly_fields = ['id', 'performed_by_user_id', 'performed_at']
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False
