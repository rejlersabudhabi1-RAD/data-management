"""
Admin configuration for Audit app
"""

from django.contrib import admin
from .models import AuditLog, SecurityEvent, ApiUsageLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_id', 'action', 'entity_type', 'entity_id',
        'status', 'timestamp',
    ]
    list_filter = ['action', 'entity_type', 'status', 'timestamp']
    search_fields = ['user_id', 'entity_id', 'ip_address', 'request_path']
    readonly_fields = [
        'id', 'user_id', 'action', 'entity_type', 'entity_id', 'status',
        'ip_address', 'user_agent', 'request_method', 'request_path',
        'response_status', 'metadata', 'timestamp',
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification - audit logs are immutable"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - audit logs are append-only"""
        return False


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'severity', 'user_id',
        'timestamp', 'resolved',
    ]
    list_filter = ['event_type', 'severity', 'resolved', 'timestamp']
    search_fields = ['user_id', 'ip_address', 'description']
    readonly_fields = [
        'id', 'event_type', 'severity', 'user_id', 'ip_address',
        'user_agent', 'description', 'request_path', 'metadata', 'timestamp',
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_type', 'severity', 'description')
        }),
        ('User Information', {
            'fields': ('user_id', 'ip_address', 'user_agent')
        }),
        ('Request Details', {
            'fields': ('request_path', 'metadata')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolved_by', 'resolution_notes')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False


@admin.register(ApiUsageLog)
class ApiUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'endpoint', 'method', 'user_id',
        'status_code', 'response_time_ms', 'timestamp',
    ]
    list_filter = ['method', 'status_code', 'timestamp']
    search_fields = ['endpoint', 'user_id']
    readonly_fields = [
        'id', 'endpoint', 'method', 'user_id',
        'status_code', 'response_time_ms', 'timestamp',
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False
