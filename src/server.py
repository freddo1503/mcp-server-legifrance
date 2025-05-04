from fastmcp import FastMCP

from src.tools.legifrance_tools import call_tool, get_prompt, list_tools

server = FastMCP("legifrance")

server.tool()(list_tools)
server.tool()(call_tool)
server.tool()(get_prompt)

if __name__ == "__main__":
    server.run(transport="sse")
