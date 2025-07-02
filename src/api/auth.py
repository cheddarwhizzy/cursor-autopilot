"""
Authentication middleware for the Cursor Autopilot API.

This module provides API key-based authentication and authorization
for protecting API endpoints.
"""

import os
import logging
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta
from flask import request, current_app
from .errors import AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API keys for authentication."""
    
    def __init__(self):
        self.api_keys = {}
        self.rate_limits = {}
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment variables."""
        # Primary API key from environment
        api_key = os.getenv('CURSOR_AUTOPILOT_API_KEY')
        if api_key:
            key_hash = self._hash_key(api_key)
            self.api_keys[key_hash] = {
                'description': 'Primary API Key',
                'created_at': datetime.now(),
                'expires_at': None,  # No expiration for primary key
                'last_used': None,
                'usage_count': 0,
                'rate_limit': 100  # requests per minute
            }
            logger.info("Loaded primary API key from environment")
        
        # Additional API keys from environment (JSON format)
        additional_keys = os.getenv('CURSOR_AUTOPILOT_API_KEYS')
        if additional_keys:
            try:
                import json
                keys_data = json.loads(additional_keys)
                for key_data in keys_data:
                    key_hash = self._hash_key(key_data['key'])
                    self.api_keys[key_hash] = {
                        'description': key_data.get('description', 'Additional API Key'),
                        'created_at': datetime.fromisoformat(key_data.get('created_at', datetime.now().isoformat())),
                        'expires_at': datetime.fromisoformat(key_data['expires_at']) if key_data.get('expires_at') else None,
                        'last_used': None,
                        'usage_count': 0,
                        'rate_limit': key_data.get('rate_limit', 100)
                    }
                logger.info(f"Loaded {len(keys_data)} additional API keys")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error loading additional API keys: {e}")
        
        if not self.api_keys:
            logger.warning("No API keys configured. API endpoints will be unprotected!")
    
    def _hash_key(self, api_key):
        """Create hash of API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_key(self, api_key):
        """
        Validate an API key and update usage statistics.
        
        Args:
            api_key (str): API key to validate
            
        Returns:
            bool: True if key is valid, False otherwise
            
        Raises:
            AuthenticationError: If key is invalid or expired
            RateLimitError: If rate limit exceeded
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        key_hash = self._hash_key(api_key)
        
        if key_hash not in self.api_keys:
            raise AuthenticationError("Invalid API key")
        
        key_info = self.api_keys[key_hash]
        
        # Check if key has expired
        if key_info['expires_at'] and datetime.now() > key_info['expires_at']:
            raise AuthenticationError("API key has expired")
        
        # Check rate limiting
        if self._is_rate_limited(key_hash, key_info['rate_limit']):
            raise RateLimitError("Rate limit exceeded for this API key")
        
        # Update usage information
        key_info['last_used'] = datetime.now()
        key_info['usage_count'] += 1
        
        logger.debug(f"API key validated successfully (usage: {key_info['usage_count']})")
        return True
    
    def _is_rate_limited(self, key_hash, limit_per_minute):
        """
        Check if API key has exceeded rate limit.
        
        Args:
            key_hash (str): Hashed API key
            limit_per_minute (int): Rate limit per minute
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize rate limit tracking for this key
        if key_hash not in self.rate_limits:
            self.rate_limits[key_hash] = []
        
        # Remove old entries
        self.rate_limits[key_hash] = [
            timestamp for timestamp in self.rate_limits[key_hash]
            if timestamp > minute_ago
        ]
        
        # Check if limit exceeded
        if len(self.rate_limits[key_hash]) >= limit_per_minute:
            return True
        
        # Add current request
        self.rate_limits[key_hash].append(now)
        return False
    
    def generate_key(self, description="Generated API Key", expires_in_days=90, rate_limit=100):
        """
        Generate a new API key.
        
        Args:
            description (str): Description of the key
            expires_in_days (int): Days until expiration (None for no expiration)
            rate_limit (int): Rate limit per minute
            
        Returns:
            str: Generated API key
        """
        api_key = secrets.token_urlsafe(32)
        key_hash = self._hash_key(api_key)
        
        self.api_keys[key_hash] = {
            'description': description,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
            'last_used': None,
            'usage_count': 0,
            'rate_limit': rate_limit
        }
        
        logger.info(f"Generated new API key: {description}")
        return api_key
    
    def list_keys(self):
        """
        List all API keys (without revealing the actual keys).
        
        Returns:
            list: List of key information dictionaries
        """
        keys = []
        for key_hash, info in self.api_keys.items():
            keys.append({
                'hash': key_hash[:8] + '...',  # Show partial hash
                'description': info['description'],
                'created_at': info['created_at'].isoformat(),
                'expires_at': info['expires_at'].isoformat() if info['expires_at'] else None,
                'last_used': info['last_used'].isoformat() if info['last_used'] else None,
                'usage_count': info['usage_count'],
                'rate_limit': info['rate_limit']
            })
        return keys

# Global API key manager instance
api_key_manager = APIKeyManager()

def require_api_key(f):
    """
    Decorator to require API key authentication for endpoints.
    
    Args:
        f (function): Flask route function to protect
        
    Returns:
        function: Wrapped function with authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication if no API keys are configured
        if not api_key_manager.api_keys:
            logger.warning("API endpoint accessed without authentication (no keys configured)")
            return f(*args, **kwargs)
        
        # Extract API key from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError("Authorization header is required")
        
        # Parse Bearer token
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError("Authorization header must start with 'Bearer '")
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate the API key
        api_key_manager.validate_key(api_key)
        
        return f(*args, **kwargs)
    
    return decorated_function

def setup_auth_middleware(app):
    """
    Set up authentication middleware for the Flask application.
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Process request before routing."""
        # Skip auth for health check and documentation endpoints
        if request.path in ['/health', '/api/docs', '/api/openapi.json']:
            return
        
        # Skip auth for Slack endpoints (they have their own validation)
        if request.path.startswith('/cursor'):
            return
        
        # Store API key manager in app context for access in routes
        current_app.api_key_manager = api_key_manager

def generate_api_key_cli():
    """CLI utility to generate a new API key."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate API key for Cursor Autopilot')
    parser.add_argument('--description', default='CLI Generated Key', help='Key description')
    parser.add_argument('--days', type=int, default=90, help='Days until expiration (0 for no expiration)')
    parser.add_argument('--rate-limit', type=int, default=100, help='Rate limit per minute')
    
    args = parser.parse_args()
    
    expires_in_days = args.days if args.days > 0 else None
    api_key = api_key_manager.generate_key(
        description=args.description,
        expires_in_days=expires_in_days,
        rate_limit=args.rate_limit
    )
    
    print(f"Generated API Key: {api_key}")
    print(f"Description: {args.description}")
    print(f"Expires: {'Never' if not expires_in_days else f'{args.days} days'}")
    print(f"Rate Limit: {args.rate_limit} requests/minute")
    print()
    print("Add this to your environment:")
    print(f"export CURSOR_AUTOPILOT_API_KEY='{api_key}'")

if __name__ == '__main__':
    generate_api_key_cli() 