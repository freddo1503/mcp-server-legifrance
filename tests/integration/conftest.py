import pytest
from src.config import (
    LEGIFRANCE_API_URL,
    LEGIFRANCE_CLIENT_ID,
    LEGIFRANCE_CLIENT_SECRET,
    LEGIFRANCE_TOKEN_URL,
)
from src.services.api_client import LegifranceApiClient


@pytest.fixture(scope="session")
def api_client():
    client = LegifranceApiClient(
        base_url=LEGIFRANCE_API_URL,
        client_id=LEGIFRANCE_CLIENT_ID,
        client_secret=LEGIFRANCE_CLIENT_SECRET,
        token_url=LEGIFRANCE_TOKEN_URL,
    )
    return client
