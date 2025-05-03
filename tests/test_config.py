"""
Test script for the new configuration module.

This script verifies that the new configuration module works as expected.
"""

from src.config import configure_logging, logger, settings


def test_settings():
    """Test that the settings are loaded correctly."""
    # Test environment variable loading
    assert settings.api.key == "mock_api_key"
    assert settings.api.url == "mock_api_url"

    # Test default values
    assert settings.server.host is not None
    assert settings.server.port is not None

    # Test YAML configuration loading
    assert settings.yaml_config is not None
    assert len(settings.yaml_config.tools) > 0
    assert len(settings.yaml_config.prompts) > 0

    # Verify specific tools exist
    assert "rechercher_dans_texte_legal" in settings.yaml_config.tools
    assert "rechercher_code" in settings.yaml_config.tools
    assert "rechercher_jurisprudence_judiciaire" in settings.yaml_config.tools


def test_logging(tmp_path):
    """Test that the logging system works."""
    # Use a temporary file for the log
    log_file = tmp_path / "test_log.log"

    # Configure logging with file output for testing
    configure_logging(level="DEBUG", file_enabled=True, file_path=str(log_file))

    # Log some messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Check if the log file was created
    assert log_file.exists(), "Log file was not created"

    # Check log file contents
    log_content = log_file.read_text()
    assert "DEBUG" in log_content, "Debug message not found in log"
    assert "INFO" in log_content, "Info message not found in log"
    assert "WARNING" in log_content, "Warning message not found in log"
    assert "ERROR" in log_content, "Error message not found in log"
