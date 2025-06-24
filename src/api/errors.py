"""
Error handling utilities for the Cursor Autopilot API.

This module provides standardized error responses and exception handling
for all API endpoints.
"""

import logging
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message, status_code=400, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []

class ValidationError(APIError):
    """Exception for validation errors."""
    
    def __init__(self, message, errors=None):
        super().__init__(message, status_code=422, errors=errors)

class AuthenticationError(APIError):
    """Exception for authentication errors."""
    
    def __init__(self, message="Authentication required"):
        super().__init__(message, status_code=401)

class AuthorizationError(APIError):
    """Exception for authorization errors."""
    
    def __init__(self, message="Insufficient permissions"):
        super().__init__(message, status_code=403)

class NotFoundError(APIError):
    """Exception for resource not found errors."""
    
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)

class RateLimitError(APIError):
    """Exception for rate limiting errors."""
    
    def __init__(self, message="Rate limit exceeded", retry_after=60):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after

def create_error_response(message, status_code=400, errors=None):
    """
    Create a standardized error response.
    
    Args:
        message (str): Main error message
        status_code (int): HTTP status code
        errors (list, optional): List of detailed errors
        
    Returns:
        tuple: JSON response and status code
    """
    response = {
        "status": "error",
        "message": message,
        "errors": errors or []
    }
    
    # Add request context for debugging
    if request:
        response["request_id"] = getattr(request, 'request_id', None)
        response["endpoint"] = request.endpoint
        response["method"] = request.method
    
    return jsonify(response), status_code

def register_error_handlers(app):
    """
    Register error handlers with the Flask application.
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        logger.error(f"API Error: {error.message}", extra={
            'status_code': error.status_code,
            'errors': error.errors
        })
        
        response = create_error_response(
            error.message, 
            error.status_code, 
            error.errors
        )
        
        # Add retry-after header for rate limit errors
        if isinstance(error, RateLimitError):
            response[0].headers['Retry-After'] = str(error.retry_after)
        
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """Handle standard HTTP errors."""
        logger.warning(f"HTTP Error: {error.description}", extra={
            'status_code': error.code
        })
        
        return create_error_response(
            error.description or "An error occurred",
            error.code
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        logger.exception("Unexpected error occurred", extra={
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        
        # Don't expose internal error details in production
        message = "An internal server error occurred"
        return create_error_response(message, 500)
    
    @app.before_request
    def add_request_id():
        """Add unique request ID for tracing."""
        import uuid
        request.request_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Request started", extra={
            'request_id': request.request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        })
    
    @app.after_request
    def log_response(response):
        """Log response information."""
        logger.info(f"Request completed", extra={
            'request_id': getattr(request, 'request_id', None),
            'status_code': response.status_code,
            'content_length': response.content_length
        })
        
        return response 