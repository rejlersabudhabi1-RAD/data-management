"""
JWT Authentication for Data Management Service
Validates JWT tokens issued by User-Management service
Does NOT issue tokens - only validates them
"""

import jwt
import logging
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)


class JWTUser:
    """
    Simple user object to hold JWT claims
    Does not interact with Django's User model
    """
    def __init__(self, user_id, role, permissions, email=None, username=None):
        self.id = user_id
        self.user_id = user_id
        self.role = role
        self.permissions = permissions or []
        self.email = email
        self.username = username
        self.is_authenticated = True
    
    def __str__(self):
        return f"JWTUser(id={self.user_id}, role={self.role})"
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def has_role(self, *roles):
        """Check if user has any of the specified roles"""
        return self.role in roles


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT Authentication class for DRF
    Extracts and validates JWT from Authorization header
    """
    
    authentication_header_prefix = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from header
            prefix, token = auth_header.split()
            
            if prefix.lower() != self.authentication_header_prefix.lower():
                logger.warning(f"Invalid authentication prefix: {prefix}")
                return None
            
            # Decode and validate token
            payload = self._decode_token(token)
            
            # Extract user information from payload
            user = self._create_user_from_payload(payload)
            
            return (user, token)
            
        except ValueError:
            logger.error("Invalid Authorization header format")
            raise exceptions.AuthenticationFailed('Invalid Authorization header format')
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def _decode_token(self, token):
        """
        Decode and validate JWT token
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'require_exp': True,
                }
            )
            
            # Validate issuer if configured
            if hasattr(settings, 'JWT_ISSUER') and settings.JWT_ISSUER:
                if payload.get('iss') != settings.JWT_ISSUER:
                    raise jwt.InvalidIssuerError('Invalid token issuer')
            
            # Validate audience if configured
            if hasattr(settings, 'JWT_AUDIENCE') and settings.JWT_AUDIENCE:
                if payload.get('aud') != settings.JWT_AUDIENCE:
                    raise jwt.InvalidAudienceError('Invalid token audience')
            
            return payload
            
        except jwt.DecodeError:
            raise jwt.InvalidTokenError('Token decode failed')
    
    def _create_user_from_payload(self, payload):
        """
        Create JWTUser object from token payload
        Expected payload structure:
        {
            'user_id': 123,
            'role': 'admin',
            'permissions': ['read', 'write'],
            'email': 'user@example.com',
            'username': 'username',
            'exp': 1234567890,
            'iss': 'user-management-service',
            'aud': 'radai-platform'
        }
        """
        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Token missing user_id')
        
        role = payload.get('role', 'user')
        permissions = payload.get('permissions', [])
        email = payload.get('email')
        username = payload.get('username')
        
        return JWTUser(
            user_id=user_id,
            role=role,
            permissions=permissions,
            email=email,
            username=username
        )
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthorized response.
        """
        return f'{self.authentication_header_prefix} realm="api"'
