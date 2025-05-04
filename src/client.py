"""Client for the MCP server using Server-Sent Events (SSE)."""

import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    async with sse_client(url="http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.send_ping()
            tools = await session.list_tools()

            for tool in tools.tools:
                print("Name:", tool.name)
                print("Description:", tool.description)
            print()


asyncio.run(main())
