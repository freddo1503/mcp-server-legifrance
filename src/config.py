"""
Legacy configuration module.

This module is maintained for backward compatibility.
It imports and re-exports configuration values from the new configuration module.
"""

from src.config.settings import settings

# Legifrance API configuration
LEGIFRANCE_API_URL = settings.legifrance.api_url
LEGIFRANCE_CLIENT_ID = settings.legifrance.client_id
LEGIFRANCE_CLIENT_SECRET = settings.legifrance.client_secret
LEGIFRANCE_TOKEN_URL = settings.legifrance.token_url

# MCP Server configuration
MCP_SERVER_HOST = settings.server.host
MCP_SERVER_PORT = settings.server.port

# Development API configuration
API_KEY = settings.api.key
API_URL = settings.api.url
