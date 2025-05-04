"""
Utility functions for the MCP server.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

import yaml

T = TypeVar("T")


def clean_dict(d: dict) -> dict:
    """
    Supprime les clés dont la valeur est None pour optimiser les requêtes API.

    Args:
        d (dict): Dictionnaire à nettoyer

    Returns:
        dict: Dictionnaire sans les valeurs None

    Example:
        >>> clean_dict({"a": 1, "b": None, "c": "test"})
        {'a': 1, 'c': 'test'}
    """
    return {k: v for k, v in d.items() if v is not None}


def rate_limit(calls: int, period: float):
    """
    Décorateur pour limiter le nombre d'appels API dans une période donnée.
    Utile pour respecter les limites de taux d'appels des API externes.

    Args:
        calls (int): Nombre maximum d'appels autorisés
        period (float): Période en secondes

    Returns:
        Callable: Décorateur qui peut être appliqué à une fonction asynchrone

    Example:
        >>> @rate_limit(calls=5, period=1.0)
        ... async def api_call():
        ...     return await some_api_request()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        last_reset = datetime.now()
        calls_made = 0

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            """
            Wrapper qui limite le taux d'appels à la fonction décorée.
            Attend si nécessaire pour respecter la limite définie.
            """
            nonlocal last_reset, calls_made
            now = datetime.now()

            elapsed_time = (now - last_reset).total_seconds()
            if elapsed_time > period:
                calls_made = 0
                last_reset = now

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


def load_prompt_templates(template_path: str | Path | None = None) -> dict:
    """
    Load prompt templates from a YAML file.

    Args:
        template_path (str | Path, optional): Path to the YAML template file.
            If None, uses the default path in the prompts directory.

    Returns:
        dict: Dictionary containing the prompt templates
    """
    if template_path is None:
        template_path = (
            Path(__file__).parent.parent / "prompts" / "prompt_templates.yml"
        )

    with open(template_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
