import os
import subprocess
import time

import pytest_asyncio

os.environ["DEV_API_KEY"] = "mock_api_key"
os.environ["DEV_API_URL"] = "mock_api_url"


@pytest_asyncio.fixture
async def server():
    """
    Starts the application server for each test function.
    """
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "src.app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(1)
    try:
        yield
    finally:
        process.kill()
        process.wait()
