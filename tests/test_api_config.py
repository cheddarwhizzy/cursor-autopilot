"""
Tests for the configuration API endpoints.

This module tests the REST API endpoints for managing configuration
settings through HTTP requests.
"""

import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from src.api.app import create_production_app
from src.config.loader import ConfigManager

@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_production_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def temp_config():
    """Create a temporary config file for testing."""
    config_data = {
        'general': {
            'inactivity_delay': 120,
            'debug': False,
            'active_platforms': ['cursor']
        },
        'platforms': {
            'cursor': {
                'type': 'cursor',
                'window_title': 'Cursor - Test',
                'project_path': '/tmp/test',
                'initialization_delay_seconds': 5
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path, config_data
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestHealthEndpoints:
    """Test health and info endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'cursor-autopilot-api'
    
    def test_api_info(self, client):
        """Test the API info endpoint."""
        response = client.get('/api/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Cursor Autopilot API'
        assert 'endpoints' in data

class TestConfigurationAPI:
    """Test configuration management API endpoints."""
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_get_config_without_auth(self, client):
        """Test getting config without authentication."""
        response = client.get('/api/config')
        assert response.status_code == 401
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_get_config_with_auth(self, client, temp_config):
        """Test getting config with proper authentication."""
        temp_path, expected_config = temp_config
        
        with patch('src.config.loader.find_config_file', return_value=temp_path):
            response = client.get('/api/config', headers={
                'Authorization': 'Bearer test-key-123'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'config' in data
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_update_config_invalid_json(self, client):
        """Test updating config with invalid JSON."""
        response = client.post('/api/config', 
                             headers={'Authorization': 'Bearer test-key-123'},
                             data="invalid json")
        
        assert response.status_code == 422  # Validation error
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_update_inactivity_delay(self, client, temp_config):
        """Test updating the inactivity delay setting."""
        temp_path, _ = temp_config
        
        with patch('src.config.loader.find_config_file', return_value=temp_path):
            # Create a temporary directory for the test
            os.makedirs('/tmp/test', exist_ok=True)
            
            update_data = {
                'general': {
                    'inactivity_delay': 300
                }
            }
            
            response = client.post('/api/config',
                                 headers={'Authorization': 'Bearer test-key-123',
                                        'Content-Type': 'application/json'},
                                 json=update_data)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'general.inactivity_delay' in data['updated_fields']
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_update_config_validation_error(self, client, temp_config):
        """Test updating config with validation errors."""
        temp_path, _ = temp_config
        
        with patch('src.config.loader.find_config_file', return_value=temp_path):
            # Invalid inactivity_delay (too small)
            update_data = {
                'general': {
                    'inactivity_delay': 30  # Below minimum of 60
                }
            }
            
            response = client.post('/api/config',
                                 headers={'Authorization': 'Bearer test-key-123',
                                        'Content-Type': 'application/json'},
                                 json=update_data)
            
            assert response.status_code == 422  # Validation error
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'validation' in data['message'].lower()

class TestAPIAuthentication:
    """Test API authentication and authorization."""
    
    def test_no_api_key_configured(self, client):
        """Test behavior when no API key is configured."""
        # Clear any existing API key
        with patch.dict(os.environ, {}, clear=True):
            response = client.get('/api/config')
            # Should allow access when no keys are configured (development mode)
            assert response.status_code in [200, 500]  # 500 if config load fails
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_missing_authorization_header(self, client):
        """Test request without Authorization header."""
        response = client.get('/api/config')
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'Authorization header is required' in data['message']
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_invalid_authorization_format(self, client):
        """Test request with invalid Authorization header format."""
        response = client.get('/api/config', headers={
            'Authorization': 'InvalidFormat test-key-123'
        })
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'Bearer' in data['message']
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_invalid_api_key(self, client):
        """Test request with invalid API key."""
        response = client.get('/api/config', headers={
            'Authorization': 'Bearer invalid-key'
        })
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'Invalid API key' in data['message']
    
    @patch.dict(os.environ, {'CURSOR_AUTOPILOT_API_KEY': 'test-key-123'})
    def test_valid_api_key(self, client, temp_config):
        """Test request with valid API key."""
        temp_path, _ = temp_config
        
        with patch('src.config.loader.find_config_file', return_value=temp_path):
            response = client.get('/api/config', headers={
                'Authorization': 'Bearer test-key-123'
            })
            
            assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__]) 