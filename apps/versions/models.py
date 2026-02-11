"""
Version models for Data Management Service
Maintains immutable version history for documents and datasets
"""

from django.db import models
import uuid


class DocumentVersion(models.Model):
    """
    Immutable version history for documents
    Stores snapshot of document at a specific point in time
    """
    
    id = models.BigAutoField(primary_key=True)
    
    # Reference to current document
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='version_history'
    )
    
    # Version information
    version_number = models.IntegerField(db_index=True)
    
    # Snapshot of document state
    file_path = models.CharField(max_length=500, help_text="S3 path to versioned file")
    file_size = models.BigIntegerField()
    checksum = models.CharField(max_length=64)
    
    # Metadata snapshot
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Version metadata
    created_by_user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    change_notes = models.TextField(blank=True, help_text="Description of changes in this version")
    
    class Meta:
        db_table = 'document_versions'
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
        indexes = [
            models.Index(fields=['document', 'version_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.document.filename} - v{self.version_number}"
    
    def save(self, *args, **kwargs):
        """Prevent modification of existing versions"""
        if self.pk:
            raise ValueError("Document versions are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of versions"""
        raise ValueError("Document versions are immutable and cannot be deleted")


class DatasetVersion(models.Model):
    """
    Immutable version history for datasets
    Stores snapshot of dataset at a specific point in time
    """
    
    id = models.BigAutoField(primary_key=True)
    
    # Reference to current dataset
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='version_history'
    )
    
    # Version information
    version_number = models.IntegerField(db_index=True)
    
    # Snapshot of dataset state
    data_snapshot = models.JSONField(help_text="Full snapshot of data at this version")
    schema_snapshot = models.JSONField(blank=True, null=True)
    
    # Statistics snapshot
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64)
    
    # Metadata snapshot
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Version metadata
    created_by_user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    change_notes = models.TextField(blank=True, help_text="Description of changes in this version")
    
    class Meta:
        db_table = 'dataset_versions'
        ordering = ['-version_number']
        unique_together = ['dataset', 'version_number']
        indexes = [
            models.Index(fields=['dataset', 'version_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.dataset.name} - v{self.version_number}"
    
    def save(self, *args, **kwargs):
        """Prevent modification of existing versions"""
        if self.pk:
            raise ValueError("Dataset versions are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of versions"""
        raise ValueError("Dataset versions are immutable and cannot be deleted")


class VersionComparison(models.Model):
    """
    Store comparison results between versions
    Used for tracking changes and diffs
    """
    
    id = models.BigAutoField(primary_key=True)
    
    # Can be either document or dataset comparison
    entity_type = models.CharField(max_length=50, choices=[
        ('document', 'Document'),
        ('dataset', 'Dataset'),
    ])
    entity_id = models.UUIDField()
    
    # Versions being compared
    version_from = models.IntegerField()
    version_to = models.IntegerField()
    
    # Comparison results
    changes = models.JSONField(help_text="Detailed changes between versions")
    summary = models.TextField(blank=True)
    
    # Metadata
    compared_by_user_id = models.IntegerField()
    compared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'version_comparisons'
        ordering = ['-compared_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['compared_at']),
        ]
    
    def __str__(self):
        return f"{self.entity_type} {self.entity_id}: v{self.version_from} -> v{self.version_to}"
