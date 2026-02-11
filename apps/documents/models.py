"""
Document models for Data Management Service
Stores document metadata and file references
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import uuid
import os


def document_upload_path(instance, filename):
    """
    Generate upload path for documents
    Format: documents/{owner_service}/{document_type}/{uuid}/{filename}
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(
        'documents',
        instance.owner_service,
        instance.document_type,
        str(instance.id),
        new_filename
    )


class Document(models.Model):
    """
    Main document model
    Stores document metadata and file location
    """
    
    DOCUMENT_TYPES = [
        ('salary_slip', 'Salary Slip'),
        ('engineering_document', 'Engineering Document'),
        ('report', 'Report'),
        ('dataset', 'Dataset'),
        ('drawing', 'Drawing'),
        ('specification', 'Specification'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, db_index=True)
    owner_service = models.CharField(max_length=100, db_index=True, help_text="Service that owns this document (e.g., 'hr', 'engineering')")
    
    # File information
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_FILE_EXTENSIONS if hasattr(settings, 'ALLOWED_FILE_EXTENSIONS') else [])],
    )
    filename = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    checksum = models.CharField(max_length=64, help_text="SHA256 checksum of file", blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata as JSON")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    
    # Versioning
    current_version = models.IntegerField(default=1)
    is_latest = models.BooleanField(default=True, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Access control
    created_by_user_id = models.IntegerField(db_index=True, help_text="User ID from User-Management service")
    created_by_role = models.CharField(max_length=50)
    is_public = models.BooleanField(default=False, help_text="Is document publicly accessible")
    allowed_roles = models.JSONField(default=list, blank=True, help_text="Roles allowed to access this document")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type', 'owner_service']),
            models.Index(fields=['created_by_user_id', 'created_at']),
            models.Index(fields=['status', 'is_latest']),
        ]
    
    def __str__(self):
        return f"{self.document_type} - {self.filename}"
    
    def save(self, *args, **kwargs):
        """Override save to set file metadata"""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get document URL"""
        if self.file:
            return self.file.url
        return None
    
    def create_new_version(self):
        """Increment version number and create history"""
        self.current_version += 1
        self.save(update_fields=['current_version', 'updated_at'])


class DocumentAccessLog(models.Model):
    """
    Log document access for compliance and audit
    Separate from main audit log for granular document tracking
    """
    
    ACCESS_TYPES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('share', 'Share'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user_id = models.IntegerField(db_index=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'document_access_logs'
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['document', 'accessed_at']),
            models.Index(fields=['user_id', 'accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.access_type} - {self.document.filename} by {self.user_id}"
