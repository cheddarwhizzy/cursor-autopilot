#!/usr/bin/env python3
"""
Test script for regular keystroke functionality.
This script tests the regular keystroke feature without requiring a full automation setup.
"""

import sys
import os
import time
import logging
from unittest.mock import MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from platforms.manager import PlatformManager
from config.loader import ConfigManager
from utils.colored_logging import setup_colored_logging


def test_regular_keystrokes():
    """Test the regular keystroke functionality."""
    # Setup logging
    setup_colored_logging(debug=True)
    logger = logging.getLogger("test_regular_keystrokes")

    logger.info("Testing regular keystroke functionality...")

    # Create mock config manager
    config_manager = MagicMock()
    config_manager.config = {
        "general": {"regular_keystroke_interval": 5}  # Use a short interval for testing
    }

    # Mock platform config with regular keystrokes
    def mock_get_platform_config(platform_name):
        if platform_name == "windsurf_test":
            return {
                "regular_keystrokes": [{"keys": "option+enter", "delay_ms": 100}],
                "regular_keystroke_interval": 3,  # Override to 3 seconds for testing
            }
        elif platform_name == "cursor_test":
            return {}  # No regular keystrokes
        return {}

    config_manager.get_platform_config = mock_get_platform_config

    # Create platform manager
    platform_manager = PlatformManager(config_manager)

    # Setup mock platform states
    current_time = time.time()
    platform_manager.platform_states = {
        "windsurf_test": {
            "regular_keystroke_interval": 3,
            "last_regular_keystroke_time": 0,  # Never sent before
        },
        "cursor_test": {
            "regular_keystroke_interval": 5,
            "last_regular_keystroke_time": current_time - 10,  # 10 seconds ago
        },
    }

    # Test 1: Check platforms needing regular keystrokes
    logger.info("Test 1: Checking platforms needing regular keystrokes...")
    platforms_needing = platform_manager.get_platforms_needing_regular_keystrokes()

    if len(platforms_needing) == 1 and platforms_needing[0]["name"] == "windsurf_test":
        logger.info(
            "✅ Test 1 PASSED: windsurf_test correctly identified as needing regular keystrokes"
        )
    else:
        logger.error(
            f"❌ Test 1 FAILED: Expected 1 platform (windsurf_test), got {len(platforms_needing)}"
        )
        return False

    # Test 2: Verify keystroke content
    logger.info("Test 2: Verifying keystroke content...")
    keystroke_data = platforms_needing[0]
    regular_keystrokes = keystroke_data["regular_keystrokes"]

    if (
        len(regular_keystrokes) == 1
        and regular_keystrokes[0]["keys"] == "option+enter"
        and regular_keystrokes[0]["delay_ms"] == 100
    ):
        logger.info("✅ Test 2 PASSED: Regular keystroke content is correct")
    else:
        logger.error(
            f"❌ Test 2 FAILED: Unexpected keystroke content: {regular_keystrokes}"
        )
        return False

    # Test 3: Update timestamp
    logger.info("Test 3: Testing timestamp update...")
    old_timestamp = platform_manager.platform_states["windsurf_test"][
        "last_regular_keystroke_time"
    ]
    platform_manager.update_regular_keystroke_time("windsurf_test")
    new_timestamp = platform_manager.platform_states["windsurf_test"][
        "last_regular_keystroke_time"
    ]

    if new_timestamp > old_timestamp:
        logger.info("✅ Test 3 PASSED: Timestamp correctly updated")
    else:
        logger.error(
            f"❌ Test 3 FAILED: Timestamp not updated. Old: {old_timestamp}, New: {new_timestamp}"
        )
        return False

    # Test 4: Check that updated platform no longer needs keystrokes
    logger.info(
        "Test 4: Verifying platforms with recent keystrokes are filtered out..."
    )
    platforms_needing_after = (
        platform_manager.get_platforms_needing_regular_keystrokes()
    )

    if len(platforms_needing_after) == 0:
        logger.info(
            "✅ Test 4 PASSED: Platform with recent keystrokes correctly filtered out"
        )
    else:
        logger.error(
            f"❌ Test 4 FAILED: Expected 0 platforms needing keystrokes, got {len(platforms_needing_after)}"
        )
        return False

    logger.info(
        "🎉 All tests passed! Regular keystroke functionality is working correctly."
    )
    return True


if __name__ == "__main__":
    success = test_regular_keystrokes()
    sys.exit(0 if success else 1)
