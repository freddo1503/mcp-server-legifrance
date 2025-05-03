import pytest

from src.config import settings
from src.services.api_client import LegifranceApiClient

LEGIFRANCE_API_URL = settings.legifrance.api_url
LEGIFRANCE_CLIENT_ID = settings.legifrance.client_id
LEGIFRANCE_CLIENT_SECRET = settings.legifrance.client_secret
LEGIFRANCE_TOKEN_URL = settings.legifrance.token_url


@pytest.fixture(scope="session")
def api_client():
    client = LegifranceApiClient(
        base_url=LEGIFRANCE_API_URL,
        client_id=LEGIFRANCE_CLIENT_ID,
        client_secret=LEGIFRANCE_CLIENT_SECRET,
        token_url=LEGIFRANCE_TOKEN_URL,
    )
    return client
