"""
Serializers for Version models
"""

from rest_framework import serializers
from .models import DocumentVersion, DatasetVersion, VersionComparison


class DocumentVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for Document versions
    """
    document_name = serializers.CharField(source='document.filename', read_only=True)
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'document', 'document_name',
            'version_number',
            'file_path', 'file_size', 'checksum',
            'metadata', 'tags',
            'created_by_user_id', 'created_by',
            'created_at', 'change_notes',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_by(self, obj):
        return {'user_id': obj.created_by_user_id}
    
    def create(self, validated_data):
        """Prevent manual creation through API"""
        raise serializers.ValidationError(
            "Versions are created automatically. Use the document's create_version endpoint."
        )
    
    def update(self, instance, validated_data):
        """Prevent updates - versions are immutable"""
        raise serializers.ValidationError("Versions are immutable and cannot be updated")


class DatasetVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for Dataset versions
    """
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = DatasetVersion
        fields = [
            'id', 'dataset', 'dataset_name',
            'version_number',
            'data_snapshot', 'schema_snapshot',
            'row_count', 'column_count', 'checksum',
            'metadata', 'tags',
            'created_by_user_id', 'created_by',
            'created_at', 'change_notes',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_by(self, obj):
        return {'user_id': obj.created_by_user_id}
    
    def create(self, validated_data):
        """Prevent manual creation through API"""
        raise serializers.ValidationError(
            "Versions are created automatically. Use the dataset's create_version endpoint."
        )
    
    def update(self, instance, validated_data):
        """Prevent updates - versions are immutable"""
        raise serializers.ValidationError("Versions are immutable and cannot be updated")


class DatasetVersionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for dataset version lists
    """
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = DatasetVersion
        fields = [
            'id', 'dataset', 'dataset_name',
            'version_number',
            'row_count', 'column_count',
            'created_by_user_id', 'created_at',
        ]


class VersionComparisonSerializer(serializers.ModelSerializer):
    """
    Serializer for version comparisons
    """
    compared_by = serializers.SerializerMethodField()
    
    class Meta:
        model = VersionComparison
        fields = [
            'id', 'entity_type', 'entity_id',
            'version_from', 'version_to',
            'changes', 'summary',
            'compared_by_user_id', 'compared_by',
            'compared_at',
        ]
        read_only_fields = ['id', 'compared_by_user_id', 'compared_at']
    
    def get_compared_by(self, obj):
        return {'user_id': obj.compared_by_user_id}
    
    def create(self, validated_data):
        """Create comparison with user context"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['compared_by_user_id'] = request.user.user_id
        
        return super().create(validated_data)
