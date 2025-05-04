#!/usr/bin/env python3
"""
Serveur MCP pour l'accès à Legifrance
-------------------------------------
Facilite l'accès aux ressources juridiques françaises via l'API Legifrance
en utilisant le protocole Model Context (MCP).

Created on Sat Apr 19 16:27:37 2025
Auteur: Raphaël d'Assignies (dassignies.law)
Date de création: Avril 2025
"""

import asyncio

import mcp.server.stdio
from mcp.server import Server

from src.config import logger, settings
from src.tools.legifrance_tools import call_tool, get_prompt, list_tools

if not settings.api.key or not settings.api.url:
    raise ValueError(
        "Les variables d'environnement DEV_API_KEY et DEV_API_URL doivent être définies"
    )

server = Server("legifrance")

server.list_tools()(list_tools)
server.call_tool()(call_tool)
server.get_prompt()(get_prompt)


async def main():
    """Point d'entrée principal du serveur MCP."""
    try:
        logger.info("Démarrage du serveur MCP Legifrance...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Erreur fatale lors de l'exécution du serveur: {e!s}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
