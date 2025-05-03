"""
Configuration module for the MCP Server.

This module provides a centralized configuration system that:
1. Loads environment variables (from .env files)
2. Loads structured config data from YAML files
3. Combines both sources into a validated configuration object
4. Initializes a logging system

Usage:
    from src.config import settings
    
    # Access configuration values
    api_url = settings.api.url
    
    # Access logger
    from src.config import logger
    logger.info("Application started")
"""

from src.config.settings import settings
from src.config.logging import logger, configure_logging

__all__ = ["settings", "logger", "configure_logging"]