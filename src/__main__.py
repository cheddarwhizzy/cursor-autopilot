#!/usr/bin/env python3
"""
Main entry point for the Cursor Autopilot application.
"""
import sys
import argparse
from src.watcher import CursorAutopilot, parse_args

def main():
    """Main entry point."""
    args = parse_args()
    app = CursorAutopilot(args)
    
    if not app.initialize():
        print("Failed to initialize Cursor Autopilot")
        return 1
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
