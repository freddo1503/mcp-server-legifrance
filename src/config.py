import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Legifrance API configuration
LEGIFRANCE_API_URL = os.getenv(
    "LEGIFRANCE_API_URL",
    "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app",
)
LEGIFRANCE_CLIENT_ID = os.getenv("LEGIFRANCE_CLIENT_ID")
LEGIFRANCE_CLIENT_SECRET = os.getenv("LEGIFRANCE_CLIENT_SECRET")
LEGIFRANCE_TOKEN_URL = os.getenv("LEGIFRANCE_TOKEN_URL")

# MCP Server configuration
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8080"))

# Development API configuration
API_KEY = os.getenv("DEV_API_KEY")
API_URL = os.getenv("DEV_API_URL")
