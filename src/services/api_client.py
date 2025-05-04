import logging
from datetime import datetime, timedelta
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from src.config import settings

T = TypeVar("T")

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API-related errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ):
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(message)


class AuthenticationError(APIError):
    """Error raised when authentication fails."""

    pass


class DataParsingError(APIError):
    """Error raised when data parsing fails."""

    pass


class LegifranceError(APIError):
    """Error raised for Legifrance-specific errors."""

    pass


class TokenInfo(BaseModel):
    """Information about an OAuth2 token."""

    access_token: str
    expires_at: datetime | None = None


class LegifranceApiClient:
    """Client for the Legifrance API with OAuth2 authentication."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the API client.

        Args:
            base_url: The base URL of the API.
            token: An existing access token.
            client_id: Client ID for token retrieval.
            client_secret: Client secret for token retrieval.
            token_url: URL to retrieve the access token.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        self.client = httpx.Client(
            headers=self._headers,
            timeout=timeout,
        )

        self._async_client = None
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url

        if token:
            self.token_info = TokenInfo(access_token=token)
        elif all([client_id, client_secret, token_url]):
            self.token_info = self._get_access_token()
        else:
            raise ValueError(
                "Either a token must be provided or client credentials and "
                "token_url must be specified."
            )

        self._headers["Authorization"] = f"Bearer {self.token_info.access_token}"
        self.client.headers["Authorization"] = f"Bearer {self.token_info.access_token}"

    @property
    def session(self) -> httpx.Client:
        """Return the httpx client for compatibility with tests."""
        return self.client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Return the async httpx client, creating it if necessary."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                headers=self._headers,
                timeout=self.timeout,
            )
        return self._async_client

    def _get_token_payload(self) -> dict[str, str]:
        """Get the payload for token requests."""
        return {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "openid",
        }

    def _process_token_response(self, token_data: dict[str, Any]) -> TokenInfo:
        """Process token response data and create a TokenInfo object."""
        if (
            not token_data.get("access_token")
            or token_data.get("access_token") == "null"
        ):
            raise AuthenticationError(
                "Failed to obtain access token", details={"response": token_data}
            )

        # Calculate token expiry with a 60-second safety margin
        expires_in = int(token_data.get("expires_in", 3600))
        expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

        return TokenInfo(
            access_token=token_data["access_token"],
            expires_at=expires_at,
        )

    def _handle_token_error(self, e: Exception) -> None:
        """
        Handle errors that occur during token retrieval.

        Args:
            e: The exception that occurred

        Raises:
            AuthenticationError: If authentication fails
            LegifranceError: For other errors
        """
        if isinstance(e, httpx.HTTPStatusError):
            details = {
                "status_code": e.response.status_code,
                "response": e.response.text,
            }

            if e.response.status_code in (401, 403):
                raise AuthenticationError(
                    "Legifrance authentication failed",
                    details=details,
                    original_exception=e,
                ) from e

            raise LegifranceError(
                f"Error obtaining Legifrance access token: "
                f"HTTP {e.response.status_code}",
                details=details,
                original_exception=e,
            ) from e

        elif isinstance(e, httpx.RequestError):
            raise LegifranceError(
                f"Error connecting to Legifrance auth server: {e}",
                original_exception=e,
            ) from e

        else:
            raise LegifranceError(
                f"Unexpected error obtaining Legifrance access token: {e}",
                original_exception=e,
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get_access_token(self) -> TokenInfo:
        """
        Retrieves an access token using client credentials and updates the token expiry.

        Returns:
            TokenInfo: Information about the access token.

        Raises:
            AuthenticationError: If authentication fails.
            LegifranceError: For other Legifrance-specific errors.
        """
        payload = self._get_token_payload()

        try:
            response = httpx.post(
                self._token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._process_token_response(response.json())

        except Exception as e:
            self._handle_token_error(e)
            # This should never be reached
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _get_access_token_async(self) -> TokenInfo:
        """
        Async version: Retrieves an access token using client credentials.

        Returns:
            TokenInfo: Information about the access token.

        Raises:
            AuthenticationError: If authentication fails.
            LegifranceError: For other Legifrance-specific errors.
        """
        payload = self._get_token_payload()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                return self._process_token_response(response.json())

        except Exception as e:
            self._handle_token_error(e)
            # This should never be reached
            raise

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        return (
            self.token_info.expires_at is not None
            and datetime.now() > self.token_info.expires_at
        )

    def _ensure_token(self) -> None:
        """Ensure the access token is valid and refresh it if expired."""
        if self._is_token_expired():
            logger.info("Access token expired, refreshing token...")
            self.token_info = self._get_access_token()
            self._update_auth_header()

    async def _ensure_token_async(self) -> None:
        """Async version: Ensure the access token is valid and refresh it if expired."""
        if self._is_token_expired():
            logger.info("Access token expired, refreshing token...")
            self.token_info = await self._get_access_token_async()
            self._update_auth_header()

    def _update_auth_header(self) -> None:
        """Update the authorization header in all clients."""
        auth_header = f"Bearer {self.token_info.access_token}"
        self._headers["Authorization"] = auth_header
        self.client.headers["Authorization"] = auth_header
        if self._async_client is not None and not self._async_client.is_closed:
            self._async_client.headers["Authorization"] = auth_header

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for an endpoint."""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _handle_request_error(self, e: Exception, method_name: str = "request") -> None:
        """
        Handle request errors and raise appropriate exceptions.

        Args:
            e: The exception that occurred
            method_name: The name of the method where the error occurred

        Raises:
            AuthenticationError: If authentication fails
            DataParsingError: If response parsing fails
            LegifranceError: For other errors
        """
        if isinstance(e, httpx.HTTPStatusError):
            details = {
                "status_code": e.response.status_code,
                "response": e.response.text,
            }

            if e.response.status_code in (401, 403):
                raise AuthenticationError(
                    "Legifrance authentication failed",
                    details=details,
                    original_exception=e,
                ) from e

            raise LegifranceError(
                f"Legifrance API {method_name} failed: HTTP {e.response.status_code}",
                details=details,
                original_exception=e,
            ) from e

        elif isinstance(e, httpx.RequestError):
            raise LegifranceError(
                f"Error connecting to Legifrance API: {e}",
                original_exception=e,
            ) from e

        elif isinstance(e, ValueError):
            raise DataParsingError(
                "Failed to parse Legifrance response as JSON",
                details={"error": str(e)},
                original_exception=e,
            ) from e
        else:
            raise LegifranceError(
                f"Unexpected error in Legifrance API {method_name}: {e}",
                original_exception=e,
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def request(
        self,
        method: str,
        endpoint: str,
        payload: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send an HTTP request and return the JSON response.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to request
            payload: Request payload (will be converted to JSON)
            params: Query parameters

        Returns:
            The JSON response as a dictionary

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            DataParsingError: If the response cannot be parsed as JSON
            APIError: For other API-related errors
        """
        self._ensure_token()
        url = self._build_url(endpoint)

        try:
            response = self.client.request(
                method=method,
                url=url,
                json=payload,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self._handle_request_error(e)
            # This should never be reached due to _handle_request_error always raising
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def request_async(
        self,
        method: str,
        endpoint: str,
        payload: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Async version: Send an HTTP request and return the JSON response.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to request
            payload: Request payload (will be converted to JSON)
            params: Query parameters

        Returns:
            The JSON response as a dictionary

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            DataParsingError: If the response cannot be parsed as JSON
            APIError: For other API-related errors
        """
        await self._ensure_token_async()
        url = self._build_url(endpoint)

        try:
            response = await self.async_client.request(
                method=method,
                url=url,
                json=payload,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            self._handle_request_error(e, method_name="async request")
            # This should never be reached due to _handle_request_error always raising
            raise

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | str:
        """
        Perform a GET request and return the response.

        Args:
            endpoint: API endpoint to request.
            params: Query parameters.

        Returns:
            The response content as a dictionary (if JSON) or string.

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            APIError: For other API-related errors
        """
        try:
            response = self.request("GET", endpoint, params=params)
            return response
        except DataParsingError:
            # If JSON parsing failed in request(), try to get the text content
            self._ensure_token()
            url = self._build_url(endpoint)
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.text

    async def get_async(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | str:
        """
        Async version: Perform a GET request and return the response.

        Args:
            endpoint: API endpoint to request.
            params: Query parameters.

        Returns:
            The response content as a dictionary (if JSON) or string.

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            APIError: For other API-related errors
        """
        try:
            response = await self.request_async("GET", endpoint, params=params)
            return response
        except DataParsingError:
            # If JSON parsing failed in request_async(), try to get the text content
            await self._ensure_token_async()
            url = self._build_url(endpoint)
            response = await self.async_client.get(url, params=params)
            response.raise_for_status()
            return response.text

    def post(
        self,
        endpoint: str,
        payload: Any = None,
    ) -> dict[str, Any]:
        """
        Perform a POST request and return the JSON response.

        Args:
            endpoint: API endpoint to request.
            payload: Request payload (will be converted to JSON).

        Returns:
            The JSON response as a dictionary.

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            DataParsingError: If the response cannot be parsed as JSON
            APIError: For other API-related errors
        """
        return self.request("POST", endpoint, payload=payload)

    async def post_async(
        self,
        endpoint: str,
        payload: Any = None,
    ) -> dict[str, Any]:
        """
        Async version: Perform a POST request and return the JSON response.

        Args:
            endpoint: API endpoint to request.
            payload: Request payload (will be converted to JSON).

        Returns:
            The JSON response as a dictionary.

        Raises:
            LegifranceError: For Legifrance-specific errors
            AuthenticationError: If authentication fails
            DataParsingError: If the response cannot be parsed as JSON
            APIError: For other API-related errors
        """
        return await self.request_async("POST", endpoint, payload=payload)

    async def aclose(self) -> None:
        """Close the async client."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()

    def __enter__(self) -> "LegifranceApiClient":
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the client when exiting the context manager."""
        self.client.close()

    async def __aenter__(self) -> "LegifranceApiClient":
        """Support for async context manager protocol."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the async client when exiting the async context manager."""
        await self.aclose()


_api_client = None


def get_api_client() -> LegifranceApiClient:
    """
    Returns a singleton instance of the LegifranceApiClient.

    The client is initialized with settings from the configuration.

    Returns:
        LegifranceApiClient: The API client instance
    """
    global _api_client
    if _api_client is None:
        _api_client = LegifranceApiClient(
            base_url=settings.legifrance.api_url,
            client_id=settings.legifrance.client_id,
            client_secret=settings.legifrance.client_secret,
            token_url=settings.legifrance.token_url,
        )
    return _api_client


async def make_api_request(endpoint: str, arguments: dict[str, Any]) -> Any:
    """
    Make an asynchronous request to the Legifrance API.

    Args:
        endpoint: The API endpoint to request (e.g., "code", "juri")
        arguments: The arguments to pass to the API

    Returns:
        The API response

    Raises:
        APIError: If the API request fails
    """
    client = get_api_client()
    try:
        return await client.post_async(f"/consult/{endpoint}", payload=arguments)
    except APIError as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}
