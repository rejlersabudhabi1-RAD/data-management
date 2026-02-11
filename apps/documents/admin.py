"""
Admin configuration for Documents app
"""

from django.contrib import admin
from .models import Document, DocumentAccessLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'filename', 'document_type', 'owner_service',
        'file_size', 'current_version', 'status',
        'created_by_user_id', 'created_at',
    ]
    list_filter = ['document_type', 'owner_service', 'status', 'is_public', 'created_at']
    search_fields = ['filename', 'id', 'created_by_user_id']
    readonly_fields = [
        'id', 'checksum', 'file_size', 'current_version',
        'created_at', 'updated_at',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'document_type', 'owner_service', 'status')
        }),
        ('File Information', {
            'fields': ('file', 'filename', 'file_size', 'mime_type', 'checksum')
        }),
        ('Metadata', {
            'fields': ('metadata', 'tags')
        }),
        ('Versioning', {
            'fields': ('current_version', 'is_latest')
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


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'document', 'user_id', 'access_type',
        'ip_address', 'accessed_at',
    ]
    list_filter = ['access_type', 'accessed_at']
    search_fields = ['document__filename', 'user_id', 'ip_address']
    readonly_fields = ['id', 'document', 'user_id', 'access_type', 'ip_address', 'user_agent', 'accessed_at']
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - append-only"""
        return False
