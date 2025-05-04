from src.config import configure_logging, logger, settings


def test_settings():
    """Test that the settings are loaded correctly."""
    assert settings.api.key == "mock_api_key"
    assert settings.api.url == "mock_api_url"

    assert settings.server.host is not None
    assert settings.server.port is not None


def test_logging(tmp_path):
    """Test that the logging system works."""
    log_file = tmp_path / "test_log.log"

    configure_logging(level="DEBUG", file_enabled=True, file_path=str(log_file))

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    assert log_file.exists(), "Log file was not created"

    log_content = log_file.read_text()
    assert "DEBUG" in log_content, "Debug message not found in log"
    assert "INFO" in log_content, "Info message not found in log"
    assert "WARNING" in log_content, "Warning message not found in log"
    assert "ERROR" in log_content, "Error message not found in log"
