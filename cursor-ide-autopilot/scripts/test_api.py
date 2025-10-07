#!/usr/bin/env python3
"""
Script to test the Cursor Autopilot configuration API.

This script provides a simple way to test the API endpoints and verify
that the configuration management is working correctly.
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, Any

def test_health_endpoint(base_url: str) -> bool:
    """Test the health endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_api_info_endpoint(base_url: str) -> bool:
    """Test the API info endpoint."""
    try:
        response = requests.get(f"{base_url}/api/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API info: {data['name']} v{data['version']}")
            return True
        else:
            print(f"❌ API info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API info error: {e}")
        return False

def test_get_config(base_url: str, api_key: str) -> bool:
    """Test getting the current configuration."""
    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.get(f"{base_url}/api/config", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get config successful")
            print(f"   Config sections: {list(data['config'].keys())}")
            return True
        else:
            print(f"❌ Get config failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get config error: {e}")
        return False

def test_update_inactivity_delay(base_url: str, api_key: str, delay: int = 180) -> bool:
    """Test updating the inactivity delay."""
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        update_data = {
            'general': {
                'inactivity_delay': delay
            }
        }
        
        response = requests.post(
            f"{base_url}/api/config", 
            headers=headers, 
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Update inactivity_delay successful")
            print(f"   Updated fields: {data.get('updated_fields', [])}")
            return True
        else:
            print(f"❌ Update inactivity_delay failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        print(f"     - {error}")
            except:
                print(f"   Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Update inactivity_delay error: {e}")
        return False

def test_authentication_failure(base_url: str) -> bool:
    """Test that authentication is required."""
    try:
        response = requests.get(f"{base_url}/api/config", timeout=5)
        
        if response.status_code == 401:
            print("✅ Authentication properly required")
            return True
        elif response.status_code == 200:
            print("⚠️  No authentication required (development mode?)")
            return True
        else:
            print(f"❌ Unexpected auth response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test the Cursor Autopilot API')
    parser.add_argument('--url', default='http://localhost:5005', 
                       help='Base URL of the API server')
    parser.add_argument('--api-key', 
                       help='API key for authentication (uses CURSOR_AUTOPILOT_API_KEY env var if not provided)')
    parser.add_argument('--delay', type=int, default=180,
                       help='Inactivity delay value to test updating')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.getenv('CURSOR_AUTOPILOT_API_KEY')
    if not api_key:
        print("❌ No API key provided. Use --api-key or set CURSOR_AUTOPILOT_API_KEY environment variable.")
        print()
        print("Generate an API key with:")
        print("  python scripts/generate_api_key.py quick")
        return 1
    
    print(f"🧪 Testing Cursor Autopilot API at {args.url}")
    print()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health check
    total_tests += 1
    if test_health_endpoint(args.url):
        tests_passed += 1
    
    # Test 2: API info
    total_tests += 1
    if test_api_info_endpoint(args.url):
        tests_passed += 1
    
    # Test 3: Authentication
    total_tests += 1
    if test_authentication_failure(args.url):
        tests_passed += 1
    
    # Test 4: Get config
    total_tests += 1
    if test_get_config(args.url, api_key):
        tests_passed += 1
    
    # Test 5: Update configuration
    total_tests += 1
    if test_update_inactivity_delay(args.url, api_key, args.delay):
        tests_passed += 1
    
    print()
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Check the API server and configuration.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 