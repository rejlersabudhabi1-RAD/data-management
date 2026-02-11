"""
Serializers for Audit models
"""

from rest_framework import serializers
from .models import AuditLog, SecurityEvent, ApiUsageLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for Audit logs
    Read-only - audit logs cannot be created or modified via API
    """
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_id', 'action',
            'entity_type', 'entity_id', 'status',
            'ip_address', 'user_agent',
            'request_method', 'request_path', 'response_status',
            'metadata', 'timestamp',
        ]
        read_only_fields = '__all__'
    
    def create(self, validated_data):
        """Prevent manual creation via API"""
        raise serializers.ValidationError(
            "Audit logs are created automatically and cannot be created manually"
        )
    
    def update(self, instance, validated_data):
        """Prevent updates - audit logs are immutable"""
        raise serializers.ValidationError("Audit logs are immutable and cannot be updated")


class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for audit log lists
    """
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_id', 'action', 'entity_type', 'entity_id',
            'status', 'timestamp',
        ]
        read_only_fields = '__all__'


class SecurityEventSerializer(serializers.ModelSerializer):
    """
    Serializer for Security events
    """
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'severity',
            'user_id', 'ip_address', 'user_agent',
            'description', 'request_path', 'metadata',
            'timestamp',
            'resolved', 'resolved_at', 'resolved_by', 'resolution_notes',
        ]
        read_only_fields = [
            'id', 'event_type', 'severity', 'user_id', 'ip_address',
            'user_agent', 'description', 'request_path', 'metadata', 'timestamp',
        ]
    
    def update(self, instance, validated_data):
        """Only allow updating resolution fields"""
        allowed_fields = ['resolved', 'resolved_at', 'resolved_by', 'resolution_notes']
        
        for field, value in validated_data.items():
            if field in allowed_fields:
                setattr(instance, field, value)
        
        instance.save()
        return instance


class SecurityEventListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for security event lists
    """
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'severity', 'user_id',
            'description', 'timestamp', 'resolved',
        ]
        read_only_fields = '__all__'


class ApiUsageLogSerializer(serializers.ModelSerializer):
    """
    Serializer for API usage logs
    """
    
    class Meta:
        model = ApiUsageLog
        fields = [
            'id', 'endpoint', 'method', 'user_id',
            'status_code', 'response_time_ms', 'timestamp',
        ]
        read_only_fields = '__all__'
