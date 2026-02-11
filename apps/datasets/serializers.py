"""
Serializers for Dataset models
"""

from rest_framework import serializers
from .models import Dataset, DatasetTransformation
import hashlib
import json


class DatasetSerializer(serializers.ModelSerializer):
    """
    Full serializer for Dataset model
    """
    created_by = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = [
            'id', 'name', 'description',
            'dataset_type', 'domain', 'source_service',
            'format', 'data', 'schema',
            'file', 'file_size', 'checksum',
            'version', 'parent_dataset', 'is_latest',
            'metadata', 'tags', 'row_count', 'column_count',
            'status',
            'created_by_user_id', 'created_by_role', 'created_by',
            'is_public', 'allowed_roles',
            'created_at', 'updated_at',
            'stats',
        ]
        read_only_fields = [
            'id', 'version', 'parent_dataset', 'file_size', 'checksum',
            'row_count', 'column_count',
            'created_by_user_id', 'created_by_role',
            'created_at', 'updated_at',
        ]
    
    def get_created_by(self, obj):
        return {
            'user_id': obj.created_by_user_id,
            'role': obj.created_by_role,
        }
    
    def get_stats(self, obj):
        return {
            'row_count': obj.row_count,
            'column_count': obj.column_count,
            'version': obj.version,
        }
    
    def validate_data(self, value):
        """Validate data structure"""
        if not isinstance(value, (dict, list)):
            raise serializers.ValidationError("Data must be a JSON object or array")
        
        # Size limit check (10MB for JSON data)
        data_size = len(json.dumps(value).encode('utf-8'))
        if data_size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Dataset size cannot exceed 10MB")
        
        return value
    
    def validate(self, attrs):
        """Validate schema if present"""
        if 'schema' in attrs and attrs['schema'] and 'data' in attrs:
            try:
                import jsonschema
                jsonschema.validate(instance=attrs['data'], schema=attrs['schema'])
            except jsonschema.ValidationError as e:
                raise serializers.ValidationError({'schema': f'Schema validation failed: {str(e)}'})
            except Exception as e:
                raise serializers.ValidationError({'schema': f'Invalid schema: {str(e)}'})
        
        return attrs
    
    def create(self, validated_data):
        """Create dataset with user context"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by_user_id'] = request.user.user_id
            validated_data['created_by_role'] = request.user.role
        
        # Calculate checksum
        if 'data' in validated_data:
            data_str = json.dumps(validated_data['data'], sort_keys=True)
            validated_data['checksum'] = hashlib.sha256(data_str.encode()).hexdigest()
        
        dataset = super().create(validated_data)
        
        # Calculate statistics
        dataset.calculate_stats()
        
        return dataset


class DatasetListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for dataset lists
    """
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = [
            'id', 'name', 'description',
            'dataset_type', 'domain', 'format',
            'version', 'is_latest', 'status',
            'row_count', 'column_count',
            'created_by_user_id', 'created_by',
            'created_at', 'updated_at',
        ]
    
    def get_created_by(self, obj):
        return {
            'user_id': obj.created_by_user_id,
            'role': obj.created_by_role,
        }


class DatasetCreateSerializer(serializers.Serializer):
    """
    Serializer for creating datasets with validation
    """
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    dataset_type = serializers.ChoiceField(choices=Dataset.DATASET_TYPES)
    domain = serializers.ChoiceField(choices=Dataset.DOMAINS)
    source_service = serializers.CharField(max_length=100)
    format = serializers.ChoiceField(choices=Dataset.FORMAT_CHOICES, default='json')
    data = serializers.JSONField()
    schema = serializers.JSONField(required=False, allow_null=True)
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
    
    def validate_data(self, value):
        """Validate data"""
        if not isinstance(value, (dict, list)):
            raise serializers.ValidationError("Data must be a JSON object or array")
        
        data_size = len(json.dumps(value).encode('utf-8'))
        if data_size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Dataset size cannot exceed 10MB")
        
        return value
    
    def validate(self, attrs):
        """Validate schema against data"""
        if 'schema' in attrs and attrs.get('schema'):
            try:
                import jsonschema
                jsonschema.validate(instance=attrs['data'], schema=attrs['schema'])
            except jsonschema.ValidationError as e:
                raise serializers.ValidationError({'schema': f'Validation failed: {str(e)}'})
        
        return attrs
    
    def create(self, validated_data):
        """Create dataset"""
        request = self.context.get('request')
        
        # Calculate checksum
        data_str = json.dumps(validated_data['data'], sort_keys=True)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()
        
        dataset = Dataset.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            dataset_type=validated_data['dataset_type'],
            domain=validated_data['domain'],
            source_service=validated_data['source_service'],
            format=validated_data.get('format', 'json'),
            data=validated_data['data'],
            schema=validated_data.get('schema'),
            checksum=checksum,
            metadata=validated_data.get('metadata', {}),
            tags=validated_data.get('tags', []),
            is_public=validated_data.get('is_public', False),
            allowed_roles=validated_data.get('allowed_roles', []),
            created_by_user_id=request.user.user_id if request and request.user else None,
            created_by_role=request.user.role if request and request.user else 'unknown',
        )
        
        dataset.calculate_stats()
        return dataset


class DatasetTransformationSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset transformations
    """
    source_dataset_name = serializers.CharField(source='source_dataset.name', read_only=True)
    target_dataset_name = serializers.CharField(source='target_dataset.name', read_only=True)
    
    class Meta:
        model = DatasetTransformation
        fields = [
            'id', 'source_dataset', 'source_dataset_name',
            'target_dataset', 'target_dataset_name',
            'transformation_type', 'transformation_code', 'parameters',
            'performed_by_user_id', 'performed_at',
        ]
        read_only_fields = ['id', 'performed_by_user_id', 'performed_at']
    
    def create(self, validated_data):
        """Create transformation with user context"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['performed_by_user_id'] = request.user.user_id
        
        return super().create(validated_data)
