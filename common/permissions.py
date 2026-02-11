"""
Custom permissions for Data Management Service
Role-based and permission-based access control
"""

from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsAuthenticated(permissions.BasePermission):
    """
    Allow access only to authenticated users
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdmin(permissions.BasePermission):
    """
    Allow access only to admin users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'superadmin']


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to all authenticated users
    Allow write access only to admins
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admins
        return request.user.role in ['admin', 'superadmin']


class HasPermission(permissions.BasePermission):
    """
    Check if user has specific permission
    Usage: permission_classes = [HasPermission]
    Set required_permission in view
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required permission from view
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            logger.warning(f"View {view.__class__.__name__} missing required_permission attribute")
            return False
        
        return request.user.has_permission(required_permission)


class CanManageDocuments(permissions.BasePermission):
    """
    Permission to manage documents
    Checks for 'manage_documents' permission
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access requires permission
        return request.user.has_permission('manage_documents') or request.user.role in ['admin', 'superadmin']
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can access/modify specific document
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins can modify any document
        if request.user.role in ['admin', 'superadmin']:
            return True
        
        # Users can only modify their own documents
        if hasattr(obj, 'created_by_user_id'):
            return obj.created_by_user_id == request.user.user_id
        
        return False


class CanManageDatasets(permissions.BasePermission):
    """
    Permission to manage datasets
    Checks for 'manage_datasets' permission
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access requires permission
        return request.user.has_permission('manage_datasets') or request.user.role in ['admin', 'superadmin']
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can access/modify specific dataset
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins can modify any dataset
        if request.user.role in ['admin', 'superadmin']:
            return True
        
        # Users can only modify their own datasets
        if hasattr(obj, 'created_by_user_id'):
            return obj.created_by_user_id == request.user.user_id
        
        return False


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission to view audit logs
    Only admins and auditors can view audit logs
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.role in ['admin', 'superadmin', 'auditor'] or
            request.user.has_permission('view_audit_logs')
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners or admins to edit
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins can modify anything
        if request.user.role in ['admin', 'superadmin']:
            return True
        
        # Check ownership
        if hasattr(obj, 'created_by_user_id'):
            return obj.created_by_user_id == request.user.user_id
        
        return False
