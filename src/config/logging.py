"""
Logging configuration for the MCP Server.

This module provides a logging system with support for console and file output,
including rotation and log level control.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.config.settings import settings

# Create logger
logger = logging.getLogger("mcp_server")


def get_log_level(level_name: str) -> int:
    """
    Convert a log level name to a logging level.
    
    Args:
        level_name: Name of the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logging level as an integer
    """
    return getattr(logging, level_name.upper())


def configure_logging(
    level: Optional[str] = None,
    format_str: Optional[str] = None,
    file_enabled: Optional[bool] = None,
    file_path: Optional[str] = None,
    file_max_bytes: Optional[int] = None,
    file_backup_count: Optional[int] = None,
) -> logging.Logger:
    """
    Configure the logging system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Logging format string
        file_enabled: Whether to log to a file
        file_path: Path to the log file
        file_max_bytes: Maximum size of the log file before rotation
        file_backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger
    """
    # Use provided values or fall back to settings
    level = level or settings.logging.level
    format_str = format_str or settings.logging.format
    file_enabled = file_enabled if file_enabled is not None else settings.logging.file_enabled
    file_path = file_path or settings.logging.file_path
    file_max_bytes = file_max_bytes or settings.logging.file_max_bytes
    file_backup_count = file_backup_count or settings.logging.file_backup_count
    
    # Convert level name to logging level
    log_level = get_log_level(level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if file_enabled and file_path:
        # Create directory if it doesn't exist
        log_file = Path(file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=file_max_bytes,
            backupCount=file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure our logger
    logger.setLevel(log_level)
    
    return logger


# Configure logging when the module is imported
configure_logging()