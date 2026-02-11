"""
Audit models for Data Management Service
Maintains comprehensive, immutable audit trail
Append-only - no updates or deletes allowed
"""

from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Comprehensive audit log for all operations
    Immutable, append-only records
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('SHARE', 'Share'),
        ('ACCESS', 'Access'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('PENDING', 'Pending'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Who performed the action
    user_id = models.IntegerField(db_index=True, help_text="User ID from User-Management service")
    
    # What action was performed
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    
    # What entity was affected
    entity_type = models.CharField(max_length=50, db_index=True, help_text="document, dataset, etc.")
    entity_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    
    # Action outcome
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS', db_index=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context")
    
    # Timestamp (automatically set, cannot be modified)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.entity_type} by user {self.user_id} @ {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Prevent modification of existing audit logs"""
        if self.pk:
            raise ValueError("Audit logs are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs"""
        raise ValueError("Audit logs cannot be deleted (append-only)")


class SecurityEvent(models.Model):
    """
    Security-specific audit events
    Track authentication failures, unauthorized access, etc.
    """
    
    EVENT_TYPES = [
        ('AUTH_FAILURE', 'Authentication Failure'),
        ('AUTH_SUCCESS', 'Authentication Success'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('TOKEN_EXPIRED', 'Token Expired'),
        ('INVALID_TOKEN', 'Invalid Token'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='MEDIUM', db_index=True)
    
    # Who/What
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    # Details
    description = models.TextField()
    request_path = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Follow-up
    resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.IntegerField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'security_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['timestamp', 'resolved']),
        ]
    
    def __str__(self):
        return f"{self.event_type} ({self.severity}) @ {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Allow resolution updates but prevent other modifications"""
        if self.pk:
            # Only allow updating resolution fields
            original = SecurityEvent.objects.get(pk=self.pk)
            allowed_fields = ['resolved', 'resolved_at', 'resolved_by', 'resolution_notes']
            
            for field in self._meta.fields:
                if field.name not in allowed_fields and field.name != 'id':
                    setattr(self, field.name, getattr(original, field.name))
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of security events"""
        raise ValueError("Security events cannot be deleted")


class ApiUsageLog(models.Model):
    """
    Track API usage for monitoring and rate limiting
    """
    
    id = models.BigAutoField(primary_key=True)
    
    # Endpoint information
    endpoint = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10)
    
    # User information
    user_id = models.IntegerField(db_index=True)
    
    # Request/Response details
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # Usage tracking
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'api_usage_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
