import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

TOOL_NAMES = {
    "rechercher_dans_texte_legal",
    "rechercher_code",
    "rechercher_jurisprudence_judiciaire",
}


@pytest.mark.asyncio
async def test_client_returns_three_tools(server):
    """
    Ensure the client returns exactly the expected three tools.
    """
    async with sse_client(url="http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.send_ping()
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}

            assert len(tools.tools) == 3, f"Expected 3 tools, got {len(tools.tools)}"
            assert TOOL_NAMES == tool_names, f"Expected {TOOL_NAMES}, got {tool_names}"
