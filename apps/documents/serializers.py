"""
Serializers for Document models
"""

from rest_framework import serializers
from .models import Document, DocumentAccessLog
import hashlib


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for Document model
    """
    file_url = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'owner_service',
            'file', 'file_url', 'filename', 'file_size', 'mime_type', 'checksum',
            'metadata', 'tags',
            'current_version', 'is_latest', 'status',
            'created_by_user_id', 'created_by_role', 'created_by',
            'is_public', 'allowed_roles',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'file_size', 'checksum', 'current_version',
            'created_by_user_id', 'created_by_role', 'created_at', 'updated_at',
        ]
    
    def get_file_url(self, obj):
        """Get presigned URL for file access"""
        return obj.get_absolute_url()
    
    def get_created_by(self, obj):
        """Get creator information"""
        return {
            'user_id': obj.created_by_user_id,
            'role': obj.created_by_role,
        }
    
    def validate_file(self, value):
        """Validate file upload"""
        if value.size > 100 * 1024 * 1024:  # 100MB limit
            raise serializers.ValidationError("File size cannot exceed 100MB")
        return value
    
    def create(self, validated_data):
        """Create document with user context"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by_user_id'] = request.user.user_id
            validated_data['created_by_role'] = request.user.role
        
        # Calculate checksum if file is present
        if 'file' in validated_data and validated_data['file']:
            file_obj = validated_data['file']
            file_obj.seek(0)
            validated_data['checksum'] = hashlib.sha256(file_obj.read()).hexdigest()
            file_obj.seek(0)
            
            # Set original filename
            validated_data['filename'] = file_obj.name
        
        return super().create(validated_data)


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for document lists
    """
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'owner_service',
            'filename', 'file_size', 'mime_type',
            'current_version', 'status',
            'created_by_user_id', 'created_by',
            'created_at', 'updated_at',
        ]
    
    def get_created_by(self, obj):
        return {
            'user_id': obj.created_by_user_id,
            'role': obj.created_by_role,
        }


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for document upload
    """
    document_type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPES)
    owner_service = serializers.CharField(max_length=100)
    file = serializers.FileField()
    metadata = serializers.JSONField(required=False, default=dict)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    is_public = serializers.BooleanField(required=False, default=False)
    allowed_roles = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    
    def validate_file(self, value):
        """Validate file upload"""
        if value.size > 100 * 1024 * 1024:  # 100MB
            raise serializers.ValidationError("File size cannot exceed 100MB")
        return value
    
    def create(self, validated_data):
        """Create document from upload"""
        request = self.context.get('request')
        
        # Calculate checksum
        file_obj = validated_data['file']
        file_obj.seek(0)
        checksum = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        
        # Create document
        document = Document.objects.create(
            document_type=validated_data['document_type'],
            owner_service=validated_data['owner_service'],
            file=file_obj,
            filename=file_obj.name,
            file_size=file_obj.size,
            mime_type=file_obj.content_type or 'application/octet-stream',
            checksum=checksum,
            metadata=validated_data.get('metadata', {}),
            tags=validated_data.get('tags', []),
            is_public=validated_data.get('is_public', False),
            allowed_roles=validated_data.get('allowed_roles', []),
            created_by_user_id=request.user.user_id if request and request.user else None,
            created_by_role=request.user.role if request and request.user else 'unknown',
        )
        
        return document


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    """
    Serializer for document access logs
    """
    document_name = serializers.CharField(source='document.filename', read_only=True)
    
    class Meta:
        model = DocumentAccessLog
        fields = [
            'id', 'document', 'document_name',
            'user_id', 'access_type',
            'ip_address', 'user_agent',
            'accessed_at',
        ]
        read_only_fields = ['id', 'accessed_at']
