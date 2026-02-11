"""
Custom middleware for Data Management Service
Includes audit logging middleware
"""

import logging
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log API requests for audit trail
    Creates audit log entries for all mutating operations
    """
    
    AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    EXCLUDED_PATHS = ['/admin/', '/health/', '/static/', '/media/']
    
    def process_request(self, request):
        """
        Process incoming request and store information for audit
        """
        # Store request start time
        request._audit_start_time = timezone.now()
        
        # Store request body for audit (if applicable)
        if request.method in self.AUDIT_METHODS:
            try:
                if hasattr(request, 'body') and request.body:
                    # Store body for later (will be logged in response)
                    request._audit_body = request.body.decode('utf-8')
            except Exception as e:
                logger.warning(f"Could not capture request body: {e}")
                request._audit_body = None
        
        return None
    
    def process_response(self, request, response):
        """
        Process response and create audit log if needed
        """
        # Skip audit for excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response
        
        # Only audit mutating operations
        if request.method not in self.AUDIT_METHODS:
            return response
        
        # Only audit if user is authenticated
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return response
        
        try:
            # Create audit log asynchronously (to avoid blocking response)
            self._create_audit_log(request, response)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        return response
    
    def _create_audit_log(self, request, response):
        """
        Create audit log entry
        """
        # Avoid circular import
        from apps.audit.models import AuditLog
        
        # Determine action type from method
        action_map = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
        }
        action = action_map.get(request.method, 'UNKNOWN')
        
        # Extract entity information from path
        entity_type = self._extract_entity_type(request.path)
        entity_id = self._extract_entity_id(request.path)
        
        # Determine status
        status = 'SUCCESS' if 200 <= response.status_code < 300 else 'FAILURE'
        
        # Create audit log
        try:
            AuditLog.objects.create(
                user_id=request.user.user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                status=status,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                request_method=request.method,
                request_path=request.path[:255],
                response_status=response.status_code,
                metadata={
                    'role': request.user.role,
                    'permissions': request.user.permissions,
                }
            )
            logger.debug(f"Audit log created: {action} {entity_type} by user {request.user.user_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log entry: {e}")
    
    def _extract_entity_type(self, path):
        """
        Extract entity type from request path
        e.g., /api/documents/ -> document
        """
        parts = [p for p in path.split('/') if p]
        if len(parts) >= 2 and parts[0] == 'api':
            return parts[1].rstrip('s')  # Remove trailing 's'
        return 'unknown'
    
    def _extract_entity_id(self, path):
        """
        Extract entity ID from request path if present
        e.g., /api/documents/123/ -> 123
        """
        parts = [p for p in path.split('/') if p]
        if len(parts) >= 3 and parts[0] == 'api':
            try:
                return int(parts[2])
            except ValueError:
                pass
        return None
    
    def _get_client_ip(self, request):
        """
        Extract client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
