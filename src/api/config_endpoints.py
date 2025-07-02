"""
Configuration management endpoints for the Cursor Autopilot API.

This module provides REST endpoints for reading and updating configuration
settings stored in the config.yaml file.
"""

import os
import logging
import copy
from flask import Blueprint, request, jsonify, current_app
from src.config.loader import ConfigManager
from .auth import require_api_key
from .validation import ConfigValidator, validate_request_data, validate_query_params
from .errors import ValidationError, NotFoundError, APIError

logger = logging.getLogger(__name__)

# Create blueprint for configuration endpoints
config_bp = Blueprint('config', __name__)

# Global configuration manager
config_manager = ConfigManager()

@config_bp.route('/config', methods=['GET'])
@require_api_key
def get_config():
    """
    Get current configuration.
    
    Query Parameters:
        section (str, optional): Specific section to retrieve (general, platforms, slack, openai)
        platform (str, optional): Specific platform to retrieve (when section=platforms)
        exclude_sensitive (bool, optional): Exclude sensitive data like API keys (default: true)
        
    Returns:
        JSON response with current configuration
    """
    try:
        # Validate query parameters
        allowed_params = ['section', 'platform', 'exclude_sensitive']
        validate_query_params(request.args, allowed_params=allowed_params)
        
        # Load current configuration
        if not config_manager.load_config(type('Args', (), {})()):
            raise APIError("Failed to load configuration", status_code=500)
        
        config = copy.deepcopy(config_manager.config)
        
        # Filter by section if requested
        section = request.args.get('section')
        if section:
            if section not in config:
                raise NotFoundError(f"Configuration section '{section}' not found")
            
            # Handle platform-specific filtering
            if section == 'platforms':
                platform = request.args.get('platform')
                if platform:
                    if platform not in config['platforms']:
                        raise NotFoundError(f"Platform '{platform}' not found")
                    config = {section: {platform: config['platforms'][platform]}}
                else:
                    config = {section: config[section]}
            else:
                config = {section: config[section]}
        
        # Exclude sensitive data by default
        exclude_sensitive = request.args.get('exclude_sensitive', 'true').lower() == 'true'
        if exclude_sensitive:
            config = _filter_sensitive_data(config)
        
        return jsonify({
            "status": "success",
            "config": config,
            "metadata": {
                "config_path": config_manager.config_path,
                "last_modified": config_manager.last_modified,
                "section": section,
                "platform": request.args.get('platform'),
                "exclude_sensitive": exclude_sensitive
            }
        })
        
    except (ValidationError, NotFoundError, APIError) as e:
        raise e
    except Exception as e:
        logger.exception("Error getting configuration")
        raise APIError("Failed to retrieve configuration", status_code=500)

@config_bp.route('/config', methods=['POST'])
@require_api_key
def update_config():
    """
    Update configuration settings.
    
    Request Body:
        JSON object with configuration updates. Supports partial updates.
        
    Example:
        {
            "general": {
                "inactivity_delay": 300,
                "debug": true
            },
            "platforms": {
                "cursor": {
                    "project_path": "/path/to/project"
                }
            }
        }
        
    Returns:
        JSON response with update results
    """
    try:
        # Validate request data
        if not request.is_json:
            raise ValidationError("Request body must be JSON")
        
        data = request.get_json()
        validate_request_data(data)
        
        # Load current configuration
        if not config_manager.load_config(type('Args', (), {})()):
            raise APIError("Failed to load current configuration", status_code=500)
        
        # Validate the configuration update
        validator = ConfigValidator()
        validation_errors = validator.validate_config_update(data)
        
        if validation_errors:
            raise ValidationError(
                "Configuration validation failed",
                errors=validation_errors
            )
        
        # Create backup of current configuration
        backup_config = copy.deepcopy(config_manager.config)
        
        # Apply updates
        updated_fields = []
        warnings = []
        
        try:
            # Update general settings
            if 'general' in data:
                for key, value in data['general'].items():
                    if key in config_manager.config.get('general', {}):
                        old_value = config_manager.config['general'][key]
                        if old_value != value:
                            config_manager.config['general'][key] = value
                            updated_fields.append(f"general.{key}")
                            logger.info(f"Updated general.{key}: {old_value} -> {value}")
                    else:
                        # New field
                        if 'general' not in config_manager.config:
                            config_manager.config['general'] = {}
                        config_manager.config['general'][key] = value
                        updated_fields.append(f"general.{key}")
                        logger.info(f"Added new field general.{key}: {value}")
            
            # Update platform settings
            if 'platforms' in data:
                for platform_name, platform_config in data['platforms'].items():
                    if platform_name not in config_manager.config.get('platforms', {}):
                        warnings.append(f"Platform '{platform_name}' does not exist in current configuration")
                        continue
                    
                    for key, value in platform_config.items():
                        old_value = config_manager.config['platforms'][platform_name].get(key)
                        if old_value != value:
                            config_manager.config['platforms'][platform_name][key] = value
                            updated_fields.append(f"platforms.{platform_name}.{key}")
                            logger.info(f"Updated platforms.{platform_name}.{key}: {old_value} -> {value}")
            
            # Update Slack settings
            if 'slack' in data:
                if 'slack' not in config_manager.config:
                    config_manager.config['slack'] = {}
                
                for key, value in data['slack'].items():
                    old_value = config_manager.config['slack'].get(key)
                    if old_value != value:
                        config_manager.config['slack'][key] = value
                        updated_fields.append(f"slack.{key}")
                        logger.info(f"Updated slack.{key}: {old_value} -> {value}")
            
            # Update OpenAI settings
            if 'openai' in data:
                if 'openai' not in config_manager.config:
                    config_manager.config['openai'] = {}
                
                # Handle nested vision config
                if 'vision' in data['openai']:
                    if 'vision' not in config_manager.config['openai']:
                        config_manager.config['openai']['vision'] = {}
                    
                    for key, value in data['openai']['vision'].items():
                        old_value = config_manager.config['openai']['vision'].get(key)
                        if old_value != value:
                            config_manager.config['openai']['vision'][key] = value
                            updated_fields.append(f"openai.vision.{key}")
                            logger.info(f"Updated openai.vision.{key}: {old_value} -> {value}")
            
            # Persist changes to file
            if updated_fields:
                success = _write_config_to_file(config_manager.config, config_manager.config_path)
                if not success:
                    # Restore backup on write failure
                    config_manager.config = backup_config
                    raise APIError("Failed to save configuration to file", status_code=500)
                
                # Update last modified timestamp
                config_manager.last_modified = os.path.getmtime(config_manager.config_path)
                
                logger.info(f"Successfully updated configuration with {len(updated_fields)} changes")
            
            return jsonify({
                "status": "success",
                "message": f"Configuration updated successfully ({len(updated_fields)} changes)",
                "updated_fields": updated_fields,
                "warnings": warnings,
                "config": _filter_sensitive_data(config_manager.config)
            })
            
        except Exception as e:
            # Restore backup on any error
            config_manager.config = backup_config
            logger.exception("Error applying configuration updates")
            raise APIError("Failed to apply configuration updates", status_code=500)
        
    except (ValidationError, NotFoundError, APIError) as e:
        raise e
    except Exception as e:
        logger.exception("Error updating configuration")
        raise APIError("Failed to update configuration", status_code=500)

@config_bp.route('/config/inactivity-delay', methods=['POST'])
@require_api_key
def update_inactivity_delay():
    """
    Update the inactivity delay setting.
    
    Request Body:
        {
            "value": 300
        }
        
    Returns:
        JSON response with update results
    """
    try:
        # Validate request data
        if not request.is_json:
            raise ValidationError("Request body must be JSON")
        
        data = request.get_json()
        validate_request_data(data, required_fields=['value'])
        
        # Validate the value
        value = data['value']
        if not isinstance(value, int) or value < 60 or value > 3600:
            raise ValidationError("inactivity_delay must be an integer between 60 and 3600 seconds")
        
        # Update using the main config endpoint
        config_update = {
            "general": {
                "inactivity_delay": value
            }
        }
        
        # Reuse the main update logic
        return _update_config_helper(config_update)
        
    except (ValidationError, APIError) as e:
        raise e
    except Exception as e:
        logger.exception("Error updating inactivity delay")
        raise APIError("Failed to update inactivity delay", status_code=500)

@config_bp.route('/config/platforms/<platform_name>', methods=['POST'])
@require_api_key
def update_platform_config(platform_name):
    """
    Update configuration for a specific platform.
    
    Parameters:
        platform_name (str): Name of the platform to update
        
    Request Body:
        JSON object with platform configuration updates
        
    Returns:
        JSON response with update results
    """
    try:
        # Validate request data
        if not request.is_json:
            raise ValidationError("Request body must be JSON")
        
        data = request.get_json()
        validate_request_data(data)
        
        # Load current configuration to check if platform exists
        if not config_manager.load_config(type('Args', (), {})()):
            raise APIError("Failed to load current configuration", status_code=500)
        
        if platform_name not in config_manager.config.get('platforms', {}):
            raise NotFoundError(f"Platform '{platform_name}' not found")
        
        # Update using the main config endpoint
        config_update = {
            "platforms": {
                platform_name: data
            }
        }
        
        return _update_config_helper(config_update)
        
    except (ValidationError, NotFoundError, APIError) as e:
        raise e
    except Exception as e:
        logger.exception(f"Error updating platform {platform_name}")
        raise APIError(f"Failed to update platform {platform_name}", status_code=500)

@config_bp.route('/config/general', methods=['POST'])
@require_api_key
def update_general_config():
    """
    Update general configuration settings.
    
    Request Body:
        JSON object with general configuration updates
        
    Returns:
        JSON response with update results
    """
    try:
        # Validate request data
        if not request.is_json:
            raise ValidationError("Request body must be JSON")
        
        data = request.get_json()
        validate_request_data(data)
        
        # Update using the main config endpoint
        config_update = {
            "general": data
        }
        
        return _update_config_helper(config_update)
        
    except (ValidationError, APIError) as e:
        raise e
    except Exception as e:
        logger.exception("Error updating general configuration")
        raise APIError("Failed to update general configuration", status_code=500)

def _update_config_helper(config_update):
    """
    Helper function to update configuration using the main update logic.
    
    Args:
        config_update: Configuration update data
        
    Returns:
        JSON response
    """
    # Temporarily set request data for the main update function
    original_json = request.get_json
    request.get_json = lambda: config_update
    
    try:
        # Call the main update function
        return update_config()
    finally:
        # Restore original request data
        request.get_json = original_json

def _filter_sensitive_data(config):
    """
    Remove sensitive data from configuration before returning to client.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Filtered configuration dictionary
    """
    filtered_config = copy.deepcopy(config)
    
    # Filter Slack tokens
    if 'slack' in filtered_config:
        sensitive_slack_fields = ['bot_token', 'app_token']
        for field in sensitive_slack_fields:
            if field in filtered_config['slack'] and filtered_config['slack'][field]:
                filtered_config['slack'][field] = '*' * 8  # Mask with asterisks
    
    # Filter OpenAI API keys
    if 'openai' in filtered_config and 'vision' in filtered_config['openai']:
        if 'api_key' in filtered_config['openai']['vision'] and filtered_config['openai']['vision']['api_key']:
            filtered_config['openai']['vision']['api_key'] = '*' * 8  # Mask with asterisks
    
    return filtered_config

def _write_config_to_file(config, config_path):
    """
    Write configuration to YAML file.
    
    Args:
        config: Configuration dictionary to write
        config_path: Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import yaml
        
        # Create backup of original file
        backup_path = f"{config_path}.backup"
        if os.path.exists(config_path):
            import shutil
            shutil.copy2(config_path, backup_path)
            logger.debug(f"Created backup at {backup_path}")
        
        # Write new configuration
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        logger.info(f"Successfully wrote configuration to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write configuration to file: {e}")
        
        # Try to restore backup if write failed
        if os.path.exists(backup_path):
            try:
                import shutil
                shutil.copy2(backup_path, config_path)
                logger.info(f"Restored configuration from backup")
            except Exception as restore_error:
                logger.error(f"Failed to restore backup: {restore_error}")
        
        return False 