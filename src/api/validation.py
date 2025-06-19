"""
Request and response validation utilities for the Cursor Autopilot API.

This module provides validation schemas and utilities for ensuring
API requests and responses meet the expected format and constraints.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from .errors import ValidationError

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration data for API updates."""
    
    # Define valid configuration schema
    GENERAL_SCHEMA = {
        'inactivity_delay': {
            'type': int,
            'min': 60,
            'max': 3600,
            'description': 'Seconds to wait before sending continuation prompt'
        },
        'debug': {
            'type': bool,
            'description': 'Enable debug logging'
        },
        'active_platforms': {
            'type': list,
            'items': str,
            'valid_values': ['cursor', 'windsurf_mushattention', 'cursor_autopilot', 'windsurf_meanscoop'],
            'description': 'List of active platforms'
        },
        'send_message': {
            'type': bool,
            'description': 'Whether to send messages automatically'
        },
        'use_vision_api': {
            'type': bool,
            'description': 'Enable OpenAI Vision API integration'
        },
        'use_gitignore': {
            'type': bool,
            'description': 'Use .gitignore patterns for file filtering'
        },
        'staggered': {
            'type': bool,
            'description': 'Enable staggered platform execution'
        },
        'stagger_delay': {
            'type': int,
            'min': 1,
            'max': 300,
            'description': 'Delay between staggered platform starts'
        },
        'initial_delay': {
            'type': int,
            'min': 1,
            'max': 300,
            'description': 'Initial delay before starting automation'
        }
    }
    
    PLATFORM_SCHEMA = {
        'type': {
            'type': str,
            'valid_values': ['cursor', 'windsurf'],
            'required': True,
            'description': 'Platform type'
        },
        'window_title': {
            'type': str,
            'min_length': 1,
            'required': True,
            'description': 'Window title to identify the application'
        },
        'project_path': {
            'type': str,
            'validate_path': True,
            'required': True,
            'description': 'Path to the project directory'
        },
        'task_file_path': {
            'type': str,
            'description': 'Path to the task file relative to project_path'
        },
        'additional_context_path': {
            'type': str,
            'description': 'Path to additional context file relative to project_path'
        },
        'initialization_delay_seconds': {
            'type': int,
            'min': 1,
            'max': 30,
            'description': 'Seconds to wait for IDE initialization'
        },
        'initial_prompt_file_path': {
            'type': str,
            'description': 'Path to initial prompt file relative to project_path'
        },
        'continuation_prompt_file_path': {
            'type': str,
            'description': 'Path to continuation prompt file relative to project_path'
        }
    }
    
    KEYSTROKE_SCHEMA = {
        'keys': {
            'type': str,
            'required': True,
            'description': 'Keystroke combination'
        },
        'delay_ms': {
            'type': int,
            'min': 1,
            'max': 5000,
            'description': 'Delay in milliseconds after keystroke'
        }
    }
    
    def __init__(self):
        self.errors = []
    
    def validate_general_config(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate general configuration data.
        
        Args:
            data: Configuration data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for key, value in data.items():
            if key not in self.GENERAL_SCHEMA:
                errors.append(f"Unknown general configuration field: {key}")
                continue
            
            schema = self.GENERAL_SCHEMA[key]
            field_errors = self._validate_field(key, value, schema)
            errors.extend(field_errors)
        
        return errors
    
    def validate_platform_config(self, platform_name: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate platform-specific configuration data.
        
        Args:
            platform_name: Name of the platform
            data: Platform configuration data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for required fields
        for key, schema in self.PLATFORM_SCHEMA.items():
            if schema.get('required', False) and key not in data:
                errors.append(f"Missing required field for platform {platform_name}: {key}")
        
        # Validate provided fields
        for key, value in data.items():
            if key == 'initialization' or key == 'keystrokes':
                # These are arrays of keystroke objects
                if not isinstance(value, list):
                    errors.append(f"Platform {platform_name}.{key} must be a list")
                    continue
                
                for i, keystroke in enumerate(value):
                    if not isinstance(keystroke, dict):
                        errors.append(f"Platform {platform_name}.{key}[{i}] must be an object")
                        continue
                    
                    keystroke_errors = self._validate_keystroke(keystroke, f"{platform_name}.{key}[{i}]")
                    errors.extend(keystroke_errors)
            
            elif key in self.PLATFORM_SCHEMA:
                schema = self.PLATFORM_SCHEMA[key]
                field_errors = self._validate_field(f"{platform_name}.{key}", value, schema)
                errors.extend(field_errors)
            
            else:
                errors.append(f"Unknown platform configuration field: {platform_name}.{key}")
        
        return errors
    
    def validate_slack_config(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate Slack configuration data.
        
        Args:
            data: Slack configuration data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if 'enabled' in data and not isinstance(data['enabled'], bool):
            errors.append("slack.enabled must be a boolean")
        
        if 'bot_token' in data and not isinstance(data['bot_token'], str):
            errors.append("slack.bot_token must be a string")
        
        if 'app_token' in data and not isinstance(data['app_token'], str):
            errors.append("slack.app_token must be a string")
        
        if 'channels' in data:
            if not isinstance(data['channels'], list):
                errors.append("slack.channels must be a list")
            else:
                for i, channel in enumerate(data['channels']):
                    if not isinstance(channel, dict):
                        errors.append(f"slack.channels[{i}] must be an object")
                        continue
                    
                    if 'name' not in channel or not isinstance(channel['name'], str):
                        errors.append(f"slack.channels[{i}].name is required and must be a string")
                    
                    if 'id' not in channel or not isinstance(channel['id'], str):
                        errors.append(f"slack.channels[{i}].id is required and must be a string")
        
        return errors
    
    def validate_openai_config(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate OpenAI configuration data.
        
        Args:
            data: OpenAI configuration data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if 'vision' in data:
            vision_config = data['vision']
            if not isinstance(vision_config, dict):
                errors.append("openai.vision must be an object")
                return errors
            
            if 'enabled' in vision_config and not isinstance(vision_config['enabled'], bool):
                errors.append("openai.vision.enabled must be a boolean")
            
            if 'api_key' in vision_config and not isinstance(vision_config['api_key'], str):
                errors.append("openai.vision.api_key must be a string")
            
            if 'model' in vision_config and not isinstance(vision_config['model'], str):
                errors.append("openai.vision.model must be a string")
            
            if 'max_tokens' in vision_config:
                if not isinstance(vision_config['max_tokens'], int) or vision_config['max_tokens'] < 1:
                    errors.append("openai.vision.max_tokens must be a positive integer")
            
            if 'temperature' in vision_config:
                if not isinstance(vision_config['temperature'], (int, float)) or not (0 <= vision_config['temperature'] <= 2):
                    errors.append("openai.vision.temperature must be a number between 0 and 2")
        
        return errors
    
    def _validate_field(self, field_name: str, value: Any, schema: Dict[str, Any]) -> List[str]:
        """
        Validate a single field against its schema.
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            schema: Schema definition for the field
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Type validation
        expected_type = schema.get('type')
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"{field_name} must be of type {expected_type.__name__}")
            return errors  # Don't continue validation if type is wrong
        
        # Numeric range validation
        if isinstance(value, (int, float)):
            if 'min' in schema and value < schema['min']:
                errors.append(f"{field_name} must be at least {schema['min']}")
            if 'max' in schema and value > schema['max']:
                errors.append(f"{field_name} must be at most {schema['max']}")
        
        # String length validation
        if isinstance(value, str):
            if 'min_length' in schema and len(value) < schema['min_length']:
                errors.append(f"{field_name} must be at least {schema['min_length']} characters long")
            if 'max_length' in schema and len(value) > schema['max_length']:
                errors.append(f"{field_name} must be at most {schema['max_length']} characters long")
        
        # Valid values validation
        if 'valid_values' in schema and value not in schema['valid_values']:
            errors.append(f"{field_name} must be one of: {', '.join(map(str, schema['valid_values']))}")
        
        # List items validation
        if isinstance(value, list) and 'items' in schema:
            items_type = schema['items']
            for i, item in enumerate(value):
                if not isinstance(item, items_type):
                    errors.append(f"{field_name}[{i}] must be of type {items_type.__name__}")
                
                # Validate items against valid values if specified
                if 'valid_values' in schema and item not in schema['valid_values']:
                    errors.append(f"{field_name}[{i}] must be one of: {', '.join(map(str, schema['valid_values']))}")
        
        # Path validation
        if schema.get('validate_path', False) and isinstance(value, str):
            expanded_path = os.path.expanduser(value)
            if not os.path.exists(expanded_path):
                errors.append(f"{field_name} path does not exist: {value}")
            elif not os.path.isdir(expanded_path):
                errors.append(f"{field_name} must be a directory: {value}")
        
        return errors
    
    def _validate_keystroke(self, keystroke: Dict[str, Any], field_name: str) -> List[str]:
        """
        Validate a keystroke object.
        
        Args:
            keystroke: Keystroke object to validate
            field_name: Name of the field for error messages
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check required fields
        if 'keys' not in keystroke:
            errors.append(f"{field_name} is missing required field: keys")
        elif not isinstance(keystroke['keys'], str):
            errors.append(f"{field_name}.keys must be a string")
        elif not keystroke['keys'].strip():
            errors.append(f"{field_name}.keys cannot be empty")
        
        # Check optional fields
        if 'delay_ms' in keystroke:
            delay = keystroke['delay_ms']
            if not isinstance(delay, int):
                errors.append(f"{field_name}.delay_ms must be an integer")
            elif delay < 1 or delay > 5000:
                errors.append(f"{field_name}.delay_ms must be between 1 and 5000")
        
        return errors
    
    def validate_config_update(self, config_data: Dict[str, Any]) -> List[str]:
        """
        Validate a complete configuration update request.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            List of validation error messages
        """
        all_errors = []
        
        # Validate general configuration
        if 'general' in config_data:
            general_errors = self.validate_general_config(config_data['general'])
            all_errors.extend(general_errors)
        
        # Validate platform configurations
        if 'platforms' in config_data:
            if not isinstance(config_data['platforms'], dict):
                all_errors.append("platforms must be an object")
            else:
                for platform_name, platform_config in config_data['platforms'].items():
                    if not isinstance(platform_config, dict):
                        all_errors.append(f"platforms.{platform_name} must be an object")
                        continue
                    
                    platform_errors = self.validate_platform_config(platform_name, platform_config)
                    all_errors.extend(platform_errors)
        
        # Validate Slack configuration
        if 'slack' in config_data:
            slack_errors = self.validate_slack_config(config_data['slack'])
            all_errors.extend(slack_errors)
        
        # Validate OpenAI configuration
        if 'openai' in config_data:
            openai_errors = self.validate_openai_config(config_data['openai'])
            all_errors.extend(openai_errors)
        
        return all_errors

def validate_request_data(data: Dict[str, Any], required_fields: List[str] = None) -> None:
    """
    Validate basic request data structure.
    
    Args:
        data: Request data to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                errors=[f"Field '{field}' is required" for field in missing_fields]
            )

def validate_query_params(params: Dict[str, Any], allowed_params: List[str] = None, 
                         required_params: List[str] = None) -> None:
    """
    Validate query parameters.
    
    Args:
        params: Query parameters to validate
        allowed_params: List of allowed parameter names
        required_params: List of required parameter names
        
    Raises:
        ValidationError: If validation fails
    """
    if required_params:
        missing_params = [param for param in required_params if param not in params]
        if missing_params:
            raise ValidationError(
                f"Missing required query parameters: {', '.join(missing_params)}",
                errors=[f"Parameter '{param}' is required" for param in missing_params]
            )
    
    if allowed_params:
        invalid_params = [param for param in params if param not in allowed_params]
        if invalid_params:
            raise ValidationError(
                f"Invalid query parameters: {', '.join(invalid_params)}",
                errors=[f"Parameter '{param}' is not allowed" for param in invalid_params]
            ) 