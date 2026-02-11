"""
Dataset models for Data Management Service
Stores structured datasets with schema validation
"""

from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
import json


class Dataset(models.Model):
    """
    Main dataset model
    Stores structured data (JSON/CSV) with schema validation
    """
    
    DATASET_TYPES = [
        ('training', 'Training Data'),
        ('validation', 'Validation Data'),
        ('test', 'Test Data'),
        ('production', 'Production Data'),
        ('reference', 'Reference Data'),
    ]
    
    DOMAINS = [
        ('hr', 'Human Resources'),
        ('engineering', 'Engineering'),
        ('ai', 'Artificial Intelligence'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('procurement', 'Procurement'),
    ]
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('parquet', 'Parquet'),
        ('xml', 'XML'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Classification
    dataset_type = models.CharField(max_length=50, choices=DATASET_TYPES, db_index=True)
    domain = models.CharField(max_length=50, choices=DOMAINS, db_index=True)
    source_service = models.CharField(max_length=100, help_text="Service that generated this dataset")
    
    # Data format
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='json')
    data = models.JSONField(help_text="Structured data stored as JSON")
    schema = models.JSONField(blank=True, null=True, help_text="JSON Schema for validation")
    
    # File storage (optional for large datasets)
    file = models.FileField(upload_to='datasets/', blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    
    # Versioning
    version = models.IntegerField(default=1)
    parent_dataset = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        help_text="Parent dataset if this is a version"
    )
    is_latest = models.BooleanField(default=True, db_index=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    row_count = models.IntegerField(null=True, blank=True, help_text="Number of rows/records")
    column_count = models.IntegerField(null=True, blank=True, help_text="Number of columns/fields")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Access control
    created_by_user_id = models.IntegerField(db_index=True)
    created_by_role = models.CharField(max_length=50)
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'datasets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset_type', 'domain']),
            models.Index(fields=['created_by_user_id', 'created_at']),
            models.Index(fields=['status', 'is_latest']),
            models.Index(fields=['name', 'domain']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.domain}) - v{self.version}"
    
    def validate_schema(self):
        """
        Validate data against schema if present
        """
        if not self.schema:
            return True
        
        try:
            import jsonschema
            jsonschema.validate(instance=self.data, schema=self.schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Schema validation failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Schema validation error: {str(e)}")
    
    def calculate_stats(self):
        """
        Calculate dataset statistics
        """
        if isinstance(self.data, list):
            self.row_count = len(self.data)
            if self.data and isinstance(self.data[0], dict):
                self.column_count = len(self.data[0].keys())
        elif isinstance(self.data, dict):
            self.row_count = 1
            self.column_count = len(self.data.keys())
        
        self.save(update_fields=['row_count', 'column_count'])
    
    def create_version(self, new_data, user_id):
        """
        Create a new version of this dataset
        """
        # Mark current as not latest
        self.is_latest = False
        self.save(update_fields=['is_latest'])
        
        # Create new version
        new_dataset = Dataset.objects.create(
            name=self.name,
            description=self.description,
            dataset_type=self.dataset_type,
            domain=self.domain,
            source_service=self.source_service,
            format=self.format,
            data=new_data,
            schema=self.schema,
            version=self.version + 1,
            parent_dataset=self,
            metadata=self.metadata,
            tags=self.tags,
            created_by_user_id=user_id,
            created_by_role=self.created_by_role,
            is_public=self.is_public,
            allowed_roles=self.allowed_roles,
        )
        
        new_dataset.calculate_stats()
        return new_dataset


class DatasetTransformation(models.Model):
    """
    Track transformations applied to datasets
    Maintains lineage and provenance
    """
    
    TRANSFORMATION_TYPES = [
        ('filter', 'Filter'),
        ('aggregate', 'Aggregate'),
        ('join', 'Join'),
        ('transform', 'Transform'),
        ('enrich', 'Enrich'),
        ('clean', 'Clean'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    source_dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='transformations_applied'
    )
    target_dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='transformations_source'
    )
    
    transformation_type = models.CharField(max_length=50, choices=TRANSFORMATION_TYPES)
    transformation_code = models.TextField(help_text="Code or query used for transformation")
    parameters = models.JSONField(default=dict, blank=True)
    
    # Metadata
    performed_by_user_id = models.IntegerField()
    performed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dataset_transformations'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.transformation_type}: {self.source_dataset.name} -> {self.target_dataset.name}"
