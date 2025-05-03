import pytest

from src.mcp_server import get_prompt, list_tools, tools_config

# Environment variables are set in conftest.py


def test_yaml_config_loaded():
    """Test that the YAML configuration is loaded correctly."""
    assert tools_config is not None
    assert hasattr(tools_config, "tools")
    assert hasattr(tools_config, "prompts")

    assert "rechercher_dans_texte_legal" in tools_config.tools
    assert "rechercher_code" in tools_config.tools
    assert "rechercher_jurisprudence_judiciaire" in tools_config.tools

    assert "agent_juridique_expert" in tools_config.prompts


@pytest.mark.asyncio
async def test_list_tools():
    """Test that the list_tools function returns the correct tools."""
    tools = await list_tools()

    assert len(tools) == 3

    tool_names = [tool.name for tool in tools]
    assert "rechercher_dans_texte_legal" in tool_names
    assert "rechercher_code" in tool_names
    assert "rechercher_jurisprudence_judiciaire" in tool_names


@pytest.mark.asyncio
async def test_get_prompt():
    """Test that the get_prompt function returns the correct prompt."""
    prompt = await get_prompt("agent_juridique_expert", {"question": "Test question"})

    assert "messages" in prompt
    assert len(prompt["messages"]) == 2

    user_message = prompt["messages"][1]
    assert user_message["role"] == "user"
    assert len(user_message["content"]) == 1
    assert user_message["content"][0]["type"] == "text"
    assert "Test question" in user_message["content"][0]["text"]
