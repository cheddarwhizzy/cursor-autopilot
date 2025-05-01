import pytest
import requests
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.exceptions import BadRequest, Unauthorized, TooManyRequests

def test_rate_limiting():
    """Test rate limiting implementation."""
    with patch('flask_limiter.Limiter') as mock_limiter:
        # Test rate limit exceeded
        mock_limiter.return_value.limit.side_effect = TooManyRequests()
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 429
        
        # Test rate limit not exceeded
        mock_limiter.return_value.limit.side_effect = None
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code != 429

def test_authentication():
    """Test authentication flow."""
    with patch('flask_jwt_extended.verify_jwt_in_request') as mock_verify:
        # Test missing token
        mock_verify.side_effect = Unauthorized()
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 401
        
        # Test invalid token
        mock_verify.side_effect = Unauthorized('Invalid token')
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 401
        
        # Test valid token
        mock_verify.side_effect = None
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code != 401

def test_request_validation():
    """Test request validation."""
    with patch('flask.request') as mock_request:
        # Test missing required fields
        mock_request.get_json.return_value = {}
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 400
        
        # Test invalid field types
        mock_request.get_json.return_value = {
            'project_path': 123,  # Should be string
            'platform': 'invalid_platform',
            'inactivity_delay': 'not_a_number'
        }
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 400
        
        # Test valid request
        mock_request.get_json.return_value = {
            'project_path': '/valid/path',
            'platform': 'cursor',
            'inactivity_delay': 300
        }
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 200

def test_response_formatting():
    """Test response formatting."""
    with patch('flask.jsonify') as mock_jsonify:
        # Test success response
        mock_jsonify.return_value = {
            'status': 'success',
            'message': 'Configuration updated successfully',
            'config': {
                'project_path': '/valid/path',
                'platform': 'cursor',
                'inactivity_delay': 300
            }
        }
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        
        # Test error response
        mock_jsonify.return_value = {
            'status': 'error',
            'message': 'Invalid configuration',
            'errors': ['Invalid platform specified']
        }
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 400
        assert response.json()['status'] == 'error'

def test_error_handling():
    """Test error handling."""
    with patch('flask.current_app') as mock_app:
        # Test database error
        mock_app.db.session.commit.side_effect = Exception('Database error')
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 500
        
        # Test file system error
        mock_app.db.session.commit.side_effect = None
        mock_app.config.get.side_effect = IOError('File system error')
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 500
        
        # Test network error
        mock_app.config.get.side_effect = None
        mock_app.requests.post.side_effect = requests.exceptions.RequestException()
        response = requests.post('http://localhost:5000/api/config', json={})
        assert response.status_code == 503 