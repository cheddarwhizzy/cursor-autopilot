#!/usr/bin/env python3
"""Generate API keys for the Cursor Autopilot configuration API."""

import sys
import os
import secrets
import argparse

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.auth import api_key_manager

def generate_api_key(description="Generated API Key", expires_in_days=90, rate_limit=100):
    """Generate a new API key with the specified parameters."""
    expires_in_days = expires_in_days if expires_in_days > 0 else None
    api_key = api_key_manager.generate_key(
        description=description,
        expires_in_days=expires_in_days,
        rate_limit=rate_limit
    )
    return api_key

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate API keys for Cursor Autopilot')
    parser.add_argument('--description', default='CLI Generated Key', help='Key description')
    parser.add_argument('--days', type=int, default=90, help='Days until expiration (0 for no expiration)')
    parser.add_argument('--rate-limit', type=int, default=100, help='Rate limit per minute')
    
    args = parser.parse_args()
    
    api_key = generate_api_key(
        description=args.description,
        expires_in_days=args.days,
        rate_limit=args.rate_limit
    )
    
    print(f"Generated API Key: {api_key}")
    print(f"Description: {args.description}")
    print(f"Expires: {'Never' if args.days == 0 else f'{args.days} days'}")
    print(f"Rate Limit: {args.rate_limit} requests/minute")
    print()
    print("Add this to your environment:")
    print(f"export CURSOR_AUTOPILOT_API_KEY='{api_key}'")

if __name__ == '__main__':
    main() 