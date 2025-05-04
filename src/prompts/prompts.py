"""
Prompt management module for the Legifrance MCP server.

This module provides functionality for managing and rendering prompt templates
for LLM interactions.
"""

from src.config import settings
from src.config.server import app
from src.utils.utils import load_prompt_templates

tools_config = settings.yaml_config


PROMPT_TEMPLATES = load_prompt_templates()


@app.prompt(name="agent_juridique_expert")
async def get_prompt(prompt_name: str, inputs: dict) -> dict:
    """
    Retourne un prompt prédéfini pour une utilisation spécifique.

    Args:
        prompt_name (str): Nom du prompt à récupérer
        inputs (dict): Entrées pour le prompt

    Returns:
        Dict: Structure du prompt
    """
    if prompt_name not in PROMPT_TEMPLATES:
        raise ValueError(f"Prompt inconnu: {prompt_name}")

    template = PROMPT_TEMPLATES[prompt_name]

    if prompt_name != "agent_juridique_expert":
        return template

    question = inputs.get("question", "")
    for message in template["messages"]:
        if message["role"] != "user":
            continue
        for content_item in message["content"]:
            if content_item["type"] == "text":
                content_item["text"] = content_item["text"].format(question=question)
    return template
