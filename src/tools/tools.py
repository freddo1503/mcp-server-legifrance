import json
from collections.abc import Sequence
from typing import Any

from mcp.types import TextContent
from pydantic import BaseModel, Field

from src.config.logging import logger
from src.config.server import app
from src.services.api_client import make_api_request


class TextContentModel(BaseModel):
    """Model representing a text content response."""

    type: str = "text"
    text: str


class ApiRequestArgs(BaseModel):
    """Base model for API request arguments."""

    pass


class RechercherCodeArgs(ApiRequestArgs):
    """Arguments for the rechercher_code API."""

    search: str
    code_name: str
    champ: str = "ALL"
    sort: str = "PERTINENCE"
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP"
    page_size: int = Field(default=10, le=100)
    fetch_all: bool = False


class RechercherJurisprudenceJudiciaireArgs(ApiRequestArgs):
    """Arguments for the rechercher_jurisprudence_judiciaire API."""

    search: str
    publication_bulletin: list[str] | None = None
    sort: str = "PERTINENCE"
    champ: str = "ALL"
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP"
    page_size: int = Field(default=10, le=100)
    fetch_all: bool = False
    juri_keys: list[str] | None = None
    juridiction_judiciaire: list[str] | None = None


class RechercherTexteLegelArgs(ApiRequestArgs):
    """Arguments for the rechercher_dans_texte_legal API."""

    search: str
    text_id: str | None = None
    champ: str = "ALL"
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP"
    page_size: int = Field(default=10, le=100)


async def execute_api_request(
    endpoint: str, arguments: ApiRequestArgs
) -> Sequence[TextContent]:
    """
    Execute an API request and format the response.

    Args:
        endpoint: The API endpoint to request
        arguments: The arguments to pass to the API

    Returns:
        Sequence[TextContent]: Formatted API response
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        args_dict = arguments.model_dump(exclude_none=True)
        logger.info(f"Calling {endpoint} API with arguments: {json.dumps(args_dict)}")
        result = await make_api_request(endpoint, args_dict)
        return format_api_result(result)
    except Exception as e:
        error_message = f"Error executing {endpoint} API request: {e!s}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]


def format_api_result(result: Any) -> Sequence[TextContent]:
    """
    Format an API result as TextContent.

    Args:
        result: The API result to format

    Returns:
        Sequence[TextContent]: Formatted result
    """
    # Handle error responses
    if isinstance(result, dict) and "error" in result:
        return [TextContent(type="text", text=result["error"])]

    # Format the result
    if isinstance(result, str):
        return [TextContent(type="text", text=result)]
    else:
        return [
            TextContent(
                type="text", text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]


@app.tool(
    name="rechercher_code",
    description="""
    Recherche des articles juridiques dans les codes de loi français.

    Paramètres:
        - search: Termes de recherche (ex: "contrat de travail", "légitime défense")
        - code_name: Nom du code juridique (ex: "Code civil", "Code du travail")
        - champ: Champ de recherche ("ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE")
        - sort: Tri des résultats ("PERTINENCE", "DATE_ASC", "DATE_DESC")
        - type_recherche: Type de recherche
        - page_size: Nombre de résultats (max 100)
        - fetch_all: Récupérer tous les résultats

    Exemples:
        - Pour le PACS dans le Code civil:
          {search="pacte civil de solidarité", code_name="Code civil"}
    """,
)
async def rechercher_code(
    search: str,
    code_name: str,
    champ: str = "ALL",
    sort: str = "PERTINENCE",
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP",
    page_size: int = 10,
    fetch_all: bool = False,
) -> Sequence[TextContent]:
    """
    Recherche des articles juridiques dans les codes de loi français.

    Args:
        search: Termes de recherche
        code_name: Nom du code juridique
        champ: Champ de recherche
        sort: Tri des résultats
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max 100)
        fetch_all: Récupérer tous les résultats

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    # Create a validated model instance
    arguments = RechercherCodeArgs(
        search=search,
        code_name=code_name,
        champ=champ,
        sort=sort,
        type_recherche=type_recherche,
        page_size=page_size,
        fetch_all=fetch_all,
    )

    return await execute_api_request("code", arguments)


@app.tool(
    name="rechercher_jurisprudence_judiciaire",
    description="""
    Recherche des jurisprudences judiciaires dans la base JURI de Legifrance.

    Paramètres:
        - search: Termes ou numéros d'affaires à rechercher
        - publication_bulletin: Si publiée au bulletin ['T'] sinon ['F']
        - sort: Tri des résultats ("PERTINENCE", "DATE_DESC", "DATE_ASC")
        - champ: Champ de recherche ("ALL", "TITLE", "ABSTRATS", "TEXTE", "RESUMES",
          "NUM_AFFAIRE")
        - type_recherche: Type de recherche
        - page_size: Nombre de résultats (max. 100)
        - fetch_all: Récupérer tous les résultats
        - juri_keys: Mots-clés pour extraire des champs comme 'titre'. Par défaut,
          le titre, le texte et les résumés sont extraits
        - juridiction_judiciaire: Liste des juridictions à inclure parmi
          ['Cour de cassation', 'Juridictions d'appel', ]

    Exemples :
        - Obtenir un panorama de la jurisprudence par mots clés :
            search = "tierce opposition salarié société liquidation",
            page_size=100, juri_keys=['titre']
        - Obtenir toutes les jurisprudences sur la signature électronique :
            search = "signature électronique", fetch_all=True,
            juri_keys=['titre', 'sommaire']

    """,
)
async def rechercher_jurisprudence_judiciaire(
    search: str,
    publication_bulletin: list[str] | None = None,
    sort: str = "PERTINENCE",
    champ: str = "ALL",
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP",
    page_size: int = 10,
    fetch_all: bool = False,
    juri_keys: list[str] | None = None,
    juridiction_judiciaire: list[str] | None = None,
) -> Sequence[TextContent]:
    """
    Recherche des jurisprudences judiciaires dans la base JURI de Legifrance.

    Args:
        search: Termes ou numéros d'affaires à rechercher
        publication_bulletin: Si publiée au bulletin ['T'] sinon ['F']
        sort: Tri des résultats
        champ: Champ de recherche
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max. 100)
        fetch_all: Récupérer tous les résultats
        juri_keys: Mots-clés pour extraire des champs comme 'titre'
        juridiction_judiciaire: Liste des juridictions à inclure

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    # Create a validated model instance
    arguments = RechercherJurisprudenceJudiciaireArgs(
        search=search,
        publication_bulletin=publication_bulletin,
        sort=sort,
        champ=champ,
        type_recherche=type_recherche,
        page_size=page_size,
        fetch_all=fetch_all,
        juri_keys=juri_keys,
        juridiction_judiciaire=juridiction_judiciaire,
    )

    # Use the common execute_api_request function for consistency
    return await execute_api_request("juri", arguments)


@app.tool(
    name="rechercher_dans_texte_legal",
    description="""
    Recherche un article dans un texte légal (loi, ordonnance, décret, arrêté)
    par le numéro du texte et le numéro de l'article. On peut également rechercher
    des mots clés ("mots clés" séparés par des espaces) dans une loi précise (n° de loi)

    Paramètres:
        - text_id: Le numéro du texte (format AAAA-NUMERO)
        - search: Mots-clés de recherche ou numéro d'article
        - champ: Champ de recherche ("ALL", "TITLE", "TABLE", "NUM_ARTICLE", "ARTICLE")
        - type_recherche: Type de recherche ("TOUS_LES_MOTS_DANS_UN_CHAMP",
          "EXPRESSION_EXACTE", "AU_MOINS_UN_MOT")
        - page_size: Nombre de résultats (max 100)

    Exemples:
        - Pour l'article 7 de la loi 78-17:
          {text_id="78-17", search="7", champ="NUM_ARTICLE"}
        - On cherche les conditions de validité de la signature électronique :
          {search="signature électronique validité conditions"}
    """,
)
async def rechercher_dans_texte_legal(
    search: str,
    text_id: str | None = None,
    champ: str = "ALL",
    type_recherche: str = "TOUS_LES_MOTS_DANS_UN_CHAMP",
    page_size: int = 10,
) -> Sequence[TextContent]:
    """
    Recherche un article dans un texte légal (loi, ordonnance, décret, arrêté).

    Args:
        search: Mots-clés de recherche ou numéro d'article
        text_id: Le numéro du texte (format AAAA-NUMERO)
        champ: Champ de recherche
        type_recherche: Type de recherche
        page_size: Nombre de résultats (max 100)

    Returns:
        Sequence[TextContent]: Résultat de la recherche
    """
    # Create a validated model instance
    arguments = RechercherTexteLegelArgs(
        search=search,
        text_id=text_id,
        champ=champ,
        type_recherche=type_recherche,
        page_size=page_size,
    )

    return await execute_api_request("texte_legal", arguments)
