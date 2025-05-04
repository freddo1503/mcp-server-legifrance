"""
Tools module for the Legifrance MCP server.

This module provides tools for interacting with the Legifrance API.
"""

from src.tools.tools import (
    ApiRequestArgs,
    RechercherCodeArgs,
    RechercherJurisprudenceJudiciaireArgs,
    RechercherTexteLegelArgs,
    TextContentModel,
    execute_api_request,
    format_api_result,
    rechercher_code,
    rechercher_dans_texte_legal,
    rechercher_jurisprudence_judiciaire,
)

__all__ = [
    "ApiRequestArgs",
    "RechercherCodeArgs",
    "RechercherJurisprudenceJudiciaireArgs",
    "RechercherTexteLegelArgs",
    "TextContentModel",
    "execute_api_request",
    "format_api_result",
    "rechercher_code",
    "rechercher_dans_texte_legal",
    "rechercher_jurisprudence_judiciaire",
]
