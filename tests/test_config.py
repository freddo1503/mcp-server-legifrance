"""
Test script for the new configuration module.

This script verifies that the new configuration module works as expected.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set some environment variables for testing
os.environ["DEV_API_KEY"] = "test_api_key"
os.environ["DEV_API_URL"] = "https://test-api.example.com"
os.environ["LOG_LEVEL"] = "DEBUG"

# Import the configuration module
from src.config import settings, logger, configure_logging


def test_settings():
    """Test that the settings are loaded correctly."""
    print("\n=== Testing Settings ===")
    
    # Test environment variable loading
    print(f"API Key: {settings.api.key}")
    print(f"API URL: {settings.api.url}")
    
    # Test default values
    print(f"Server Host: {settings.server.host}")
    print(f"Server Port: {settings.server.port}")
    
    # Test YAML configuration loading
    if settings.yaml_config:
        print("\nYAML Configuration:")
        print(f"Number of tools: {len(settings.yaml_config.tools)}")
        print(f"Number of prompts: {len(settings.yaml_config.prompts)}")
        
        # Print the names of the tools
        print("\nTool names:")
        for tool_name in settings.yaml_config.tools:
            print(f"- {tool_name}")
    else:
        print("\nYAML Configuration not loaded")


def test_logging():
    """Test that the logging system works."""
    print("\n=== Testing Logging ===")
    
    # Configure logging with file output for testing
    configure_logging(
        level="DEBUG",
        file_enabled=True,
        file_path="test_log.log"
    )
    
    # Log some messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("Logged messages to console and test_log.log")
    
    # Check if the log file was created
    log_file = Path("test_log.log")
    if log_file.exists():
        print(f"Log file created: {log_file.absolute()}")
        
        # Print the contents of the log file
        print("\nLog file contents:")
        with open(log_file, "r") as f:
            for line in f.readlines():
                print(line.strip())
        
        # Clean up
        log_file.unlink()
        print("\nLog file deleted")


if __name__ == "__main__":
    test_settings()
    test_logging()