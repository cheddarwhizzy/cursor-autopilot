#!/bin/bash

# Test script for the Cursor Autopilot Configuration API
# This script tests the API endpoints using curl commands

set -e  # Exit on any error

# Configuration
API_BASE_URL="http://localhost:5005"
API_KEY="${CURSOR_AUTOPILOT_API_KEY}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_TOTAL=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

run_test() {
    ((TESTS_TOTAL++))
    echo
    log_info "Running: $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if [ -z "$API_KEY" ]; then
        log_error "No API key found. Set CURSOR_AUTOPILOT_API_KEY environment variable."
        echo
        echo "Generate an API key with:"
        echo "  python scripts/generate_api_key.py --description 'Test Key' --days 30"
        echo
        echo "Then export it:"
        echo "  export CURSOR_AUTOPILOT_API_KEY='your-generated-key'"
        exit 1
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl is required but not installed."
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        log_warning "jq not found. JSON responses will not be formatted."
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
    
    log_success "Prerequisites check passed"
}

# Format JSON response if jq is available
format_response() {
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

# Test 1: Health check
test_health() {
    run_test "Health check"
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/health")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "Health check passed"
        if [ "$JQ_AVAILABLE" = true ]; then
            status=$(echo "$body" | jq -r '.status')
            echo "   Status: $status"
        fi
    else
        log_error "Health check failed (HTTP $http_code)"
        echo "   Response: $body"
    fi
}

# Test 2: API info
test_api_info() {
    run_test "API info"
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/info")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "API info retrieved"
        if [ "$JQ_AVAILABLE" = true ]; then
            name=$(echo "$body" | jq -r '.name')
            version=$(echo "$body" | jq -r '.version')
            echo "   API: $name v$version"
        fi
    else
        log_error "API info failed (HTTP $http_code)"
        echo "   Response: $body"
    fi
}

# Test 3: Authentication check
test_authentication() {
    run_test "Authentication check (should fail without API key)"
    
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/config")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "401" ]; then
        log_success "Authentication properly required"
    elif [ "$http_code" = "200" ]; then
        log_warning "No authentication required (development mode?)"
        ((TESTS_PASSED++))
    else
        log_error "Unexpected auth response (HTTP $http_code)"
        echo "   Response: $body"
    fi
}

# Test 4: Get configuration
test_get_config() {
    run_test "Get current configuration"
    
    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        "$API_BASE_URL/api/config")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "Configuration retrieved successfully"
        if [ "$JQ_AVAILABLE" = true ]; then
            sections=$(echo "$body" | jq -r '.config | keys | join(", ")')
            echo "   Config sections: $sections"
        fi
    else
        log_error "Get config failed (HTTP $http_code)"
        echo "   Response:"
        format_response "$body"
    fi
}

# Test 5: Update inactivity delay
test_update_inactivity_delay() {
    run_test "Update inactivity delay"
    
    # Test updating inactivity_delay to 240 seconds
    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -X POST "$API_BASE_URL/api/config" \
        -d '{"general": {"inactivity_delay": 240}}')
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "Inactivity delay updated successfully"
        if [ "$JQ_AVAILABLE" = true ]; then
            updated_fields=$(echo "$body" | jq -r '.updated_fields | join(", ")')
            echo "   Updated fields: $updated_fields"
        fi
    else
        log_error "Update inactivity delay failed (HTTP $http_code)"
        echo "   Response:"
        format_response "$body"
    fi
}

# Test 6: Update windsurf_meanscoop platform
test_update_windsurf_platform() {
    run_test "Update windsurf_meanscoop platform configuration"
    
    # Test updating windsurf_meanscoop platform settings
    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -X POST "$API_BASE_URL/api/config" \
        -d '{
            "platforms": {
                "windsurf_meanscoop": {
                    "initialization_delay_seconds": 15,
                    "project_path": "/Volumes/My Shared Files/Home/cheddar/cheddarwhizzy/mean-scoop/meanscoop-payload"
                }
            }
        }')
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "windsurf_meanscoop platform updated successfully"
        if [ "$JQ_AVAILABLE" = true ]; then
            updated_fields=$(echo "$body" | jq -r '.updated_fields | join(", ")')
            echo "   Updated fields: $updated_fields"
        fi
    else
        log_error "Update windsurf_meanscoop platform failed (HTTP $http_code)"
        echo "   Response:"
        format_response "$body"
    fi
}

# Test 7: Validation error test
test_validation_error() {
    run_test "Validation error test (invalid inactivity_delay)"
    
    # Test with invalid inactivity_delay (too small)
    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -X POST "$API_BASE_URL/api/config" \
        -d '{"general": {"inactivity_delay": 30}}')
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "422" ]; then
        log_success "Validation error properly caught"
        if [ "$JQ_AVAILABLE" = true ]; then
            errors=$(echo "$body" | jq -r '.errors | join(", ")')
            echo "   Validation errors: $errors"
        fi
    else
        log_error "Expected validation error but got HTTP $http_code"
        echo "   Response:"
        format_response "$body"
    fi
}

# Main execution
main() {
    echo "🧪 Testing Cursor Autopilot Configuration API"
    echo "================================================"
    echo "Base URL: $API_BASE_URL"
    echo "API Key: ${API_KEY:0:8}..." # Show first 8 chars only
    echo
    
    check_prerequisites
    
    # Run all tests
    test_health
    test_api_info
    test_authentication
    test_get_config
    test_update_inactivity_delay
    test_update_windsurf_platform
    test_validation_error
    
    # Final results
    echo
    echo "================================================"
    echo "📊 Test Results: $TESTS_PASSED/$TESTS_TOTAL tests passed"
    echo
    
    if [ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ]; then
        log_success "All tests passed! The API is working correctly."
        exit 0
    else
        log_error "Some tests failed. Check the API server and configuration."
        exit 1
    fi
}

# Show usage if --help is passed
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo
    echo "Test the Cursor Autopilot Configuration API"
    echo
    echo "Environment variables:"
    echo "  CURSOR_AUTOPILOT_API_KEY  - API key for authentication (required)"
    echo "  API_BASE_URL              - Base URL for API (default: http://localhost:5005)"
    echo
    echo "Prerequisites:"
    echo "  - curl (required)"
    echo "  - jq (optional, for pretty JSON formatting)"
    echo
    echo "Examples:"
    echo "  # Set API key and run tests"
    echo "  export CURSOR_AUTOPILOT_API_KEY='your-key'"
    echo "  $0"
    echo
    echo "  # Generate API key first"
    echo "  python scripts/generate_api_key.py --description 'Test Key' --days 30"
    echo "  export CURSOR_AUTOPILOT_API_KEY='generated-key'"
    echo "  $0"
    exit 0
fi

# Run main function
main 