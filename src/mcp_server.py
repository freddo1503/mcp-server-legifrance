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
import json
from collections.abc import Sequence
from datetime import datetime
from functools import wraps
from typing import Any

import requests
import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool

from src.config import settings, logger

# Utilisation de la configuration chargée via le module de configuration
tools_config = settings.yaml_config

if not settings.api.key or not settings.api.url:
    raise ValueError(
        "Les variables d'environnement DEV_API_KEY et DEV_API_URL "
        "doivent être définies"
    )

HEADERS = {"accept": "*/*", "Content-Type": "application/json"}

# Création du serveur MCP
server = Server("legifrance")


# Utilitaires
def clean_dict(d: dict) -> dict:
    """
    Supprime les clés dont la valeur est None pour optimiser les requêtes API.

    Args:
        d (dict): Dictionnaire à nettoyer

    Returns:
        dict: Dictionnaire sans les valeurs None
    """
    return {k: v for k, v in d.items() if v is not None}


def rate_limit(calls: int, period: float):
    """
    Décorateur pour limiter le nombre d'appels API dans une période donnée.

    Args:
        calls (int): Nombre maximum d'appels autorisés
        period (float): Période en secondes
    """

    def decorator(func):
        last_reset = datetime.now()
        calls_made = 0

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            now = datetime.now()

            # Réinitialisation du compteur si la période est écoulée
            if (now - last_reset).total_seconds() > period:
                calls_made = 0
                last_reset = now

            # Si la limite est atteinte, attendre la fin de la période
            if calls_made >= calls:
                wait_time = period - (now - last_reset).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    last_reset = datetime.now()
                    calls_made = 0

            calls_made += 1
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def make_api_request(endpoint: str, data: dict) -> dict:
    """
    Fonction générique pour effectuer des requêtes API avec gestion d'erreurs.

    Args:
        endpoint (str): Point de terminaison de l'API (sans le domaine)
        data (Dict): Données à envoyer dans la requête

    Returns:
        Dict: Résultat de la requête ou message d'erreur
    """
    try:
        url = f"{settings.api.url}{endpoint}"
        clean_data = clean_dict(data)

        logger.info(
            f"Envoi de requête à {endpoint} avec les données: {json.dumps(clean_data)}"
        )

        res = requests.post(
            url,
            headers=HEADERS,
            params={"api_key": settings.api.key},
            json=clean_data,
            timeout=30,  # Timeout explicite pour éviter les blocages
        )

        content_type = res.headers.get("Content-Type", "")
        response_body = res.text

        if res.ok:
            try:
                result = res.json()
            except requests.exceptions.JSONDecodeError:
                result = response_body  # fallback sur le texte brut

            if isinstance(result, str):
                result += (
                    "\n\n🔗 Mentionne systématiquement le lien officiel "
                    "dans ta réponse pour pouvoir y accéder."
                )
            return result

        if res.status_code == 422 or res.status_code == 404:
            if "text/plain" in content_type:
                return {"error": response_body}

        if "application/json" in content_type:
            try:
                return {"error": res.json()}
            except requests.exceptions.JSONDecodeError:
                return {"error": response_body}

        return {"error": f"Erreur {res.status_code} : {response_body}"}

    except requests.exceptions.RequestException as e:
        logger.error("Erreur de connexion à l'API", exc_info=True)
        return {"error": f"Erreur de connexion : {e}"}

    except Exception as e:
        # Uniquement pour les erreurs de connexion ou autres problèmes graves
        logger.error(f"Erreur de connexion: {e!s}")
        return {"error": f"Erreur de connexion: {e!s}"}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles dans ce serveur MCP."""
    tools_list = []

    for tool_name, tool_config in tools_config.tools.items():
        tools_list.append(
            Tool(
                name=tool_config.name,
                description=tool_config.description,
                inputSchema=tool_config.input_schema,
            )
        )

    return tools_list


@server.call_tool()
@rate_limit(calls=5, period=1.0)  # Limite à 5 appels par seconde
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """
    Gère les appels aux outils juridiques.

    Args:
        name (str): Nom de l'outil à appeler
        arguments (Any): Arguments à passer à l'outil

    Returns:
        Sequence[TextContent]: Résultat de l'appel
    """
    try:
        logger.info(f"Appel de l'outil: {name} avec arguments: {json.dumps(arguments)}")

        if name == "rechercher_dans_texte_legal":
            result = await make_api_request("loda", arguments)

        elif name == "rechercher_code":
            result = await make_api_request("code", arguments)

        elif name == "rechercher_jurisprudence_judiciaire":
            result = await make_api_request("juri", arguments)

        else:
            raise ValueError(f"Outil inconnu: {name}")

        # Détection et traitement des erreurs
        if isinstance(result, dict) and "error" in result:
            return [TextContent(type="text", text=result["error"])]

        # Formatage du résultat
        if isinstance(result, str):
            return [TextContent(type="text", text=result)]
        else:
            return [
                TextContent(
                    type="text", text=json.dumps(result, indent=2, ensure_ascii=False)
                )
            ]

    except Exception as e:
        error_message = f"Erreur lors de l'exécution de {name}: {e!s}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]


@server.get_prompt()
async def get_prompt(prompt_name: str, inputs: dict) -> dict:
    """
    Retourne un prompt prédéfini pour une utilisation spécifique.

    Args:
        prompt_name (str): Nom du prompt à récupérer
        inputs (dict): Entrées pour le prompt

    Returns:
        Dict: Structure du prompt
    """
    if prompt_name in tools_config.prompts:
        prompt_config = tools_config.prompts[prompt_name]

        # Remplacer les variables dans le texte du prompt
        messages = []
        for message in prompt_config.messages:
            content_list = []
            for content_item in message.content:
                text = content_item["text"]
                # Remplacer les variables dans le texte
                for key, value in inputs.items():
                    text = text.replace(f"{{{key}}}", str(value))
                content_list.append({"type": content_item["type"], "text": text})

            messages.append({"role": message.role, "content": content_list})

        return {"messages": messages}
    else:
        raise ValueError(f"Prompt inconnu: {prompt_name}")


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
