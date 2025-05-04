"""
MCP tool implementations for the Legifrance API.
"""

import json
from collections.abc import Sequence
from typing import Any

from mcp.types import TextContent, Tool

from src.config import logger, settings
from src.services.api_client import get_api_client
from src.utils.utils import clean_dict, rate_limit

tools_config = settings.yaml_config


@rate_limit(calls=5, period=1.0)
async def call_tool(
    name: str, arguments: Any, api_client=None
) -> Sequence[TextContent]:
    """
    Gère les appels aux outils juridiques.

    Args:
        name (str): Nom de l'outil à appeler
        arguments (Any): Arguments à passer à l'outil
        api_client: Client API à utiliser pour les requêtes,
            si None, utilise make_api_request

    Returns:
        Sequence[TextContent]: Résultat de l'appel
    """
    try:
        logger.info(f"Appel de l'outil: {name} avec arguments: {json.dumps(arguments)}")

        endpoint = ""
        match name:
            case "rechercher_dans_texte_legal":
                endpoint = "loda"
            case "rechercher_code":
                endpoint = "code"
            case "rechercher_jurisprudence_judiciaire":
                endpoint = "juri"
            case _:
                raise ValueError(f"Outil inconnu: {name}")

        clean_data = clean_dict(arguments)

        logger.info(
            f"Envoi de requête à {endpoint} avec les données: {json.dumps(clean_data)}"
        )

        try:
            if api_client:
                result = await api_client(endpoint, clean_data)
            else:
                client = get_api_client()
                result = await client.post_async(endpoint, payload=clean_data)

            if isinstance(result, str):
                result += (
                    "\n\n🔗 Mentionne systématiquement le lien officiel "
                    "dans ta réponse pour pouvoir y accéder."
                )

            if isinstance(result, dict) and "error" in result:
                return [TextContent(type="text", text=result["error"])]
            elif isinstance(result, str):
                return [TextContent(type="text", text=result)]
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, ensure_ascii=False),
                    )
                ]

        except Exception as e:
            error_message = f"Erreur API lors de l'exécution de {name}: {e!s}"
            logger.error(error_message)
            return [TextContent(type="text", text=error_message)]

    except Exception as e:
        error_message = f"Erreur lors de l'exécution de {name}: {e!s}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]


async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles dans ce serveur MCP."""
    return [
        Tool(
            name=tool_config.name,
            description=tool_config.description,
            inputSchema=tool_config.input_schema,
        )
        for _tool_name, tool_config in tools_config.tools.items()
    ]


async def get_prompt(prompt_name: str, inputs: dict) -> dict:
    """
    Retourne un prompt prédéfini pour une utilisation spécifique.

    Args:
        prompt_name (str): Nom du prompt à récupérer
        inputs (dict): Entrées pour le prompt

    Returns:
        dict: Structure du prompt
    """
    match tools_config.prompts.get(prompt_name):
        case None:
            raise ValueError(f"Prompt inconnu: {prompt_name}")
        case prompt_config:
            messages = [
                {
                    "role": message.role,
                    "content": [
                        {
                            "type": item["type"],
                            "text": _replace_variables(item["text"], inputs),
                        }
                        for item in message.content
                    ],
                }
                for message in prompt_config.messages
            ]

            return {"messages": messages}


def _replace_variables(text: str, variables: dict) -> str:
    """
    Remplace les variables dans un texte par leurs valeurs.

    Args:
        text (str): Texte contenant des variables sous forme {nom_variable}
        variables (dict): Dictionnaire des variables et leurs valeurs

    Returns:
        str: Texte avec les variables remplacées
    """
    for key, value in variables.items():
        text = text.replace(f"{{{key}}}", str(value))
    return text
