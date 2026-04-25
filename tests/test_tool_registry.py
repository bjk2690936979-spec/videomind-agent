import pytest

from backend.tools.registry import ToolRegistry, default_registry


def test_list_tools_returns_registered_tools() -> None:
    tools = default_registry.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "extract_subtitle" in tool_names
    assert "whisper_fallback" in tool_names
    assert "generate_summary" in tool_names


def test_get_extract_subtitle_tool_definition() -> None:
    tool = default_registry.get_tool("extract_subtitle")

    assert tool.name == "extract_subtitle"
    assert tool.description
    assert "video_url" in tool.input_schema
    assert "transcript" in tool.output_schema
    assert tool.handler is not None


def test_get_unknown_tool_has_clear_error() -> None:
    with pytest.raises(KeyError, match="Tool not registered"):
        default_registry.get_tool("missing_tool")


def test_tool_metadata_contains_required_fields() -> None:
    for tool in default_registry.list_tools():
        assert tool.name
        assert tool.description
        assert isinstance(tool.input_schema, dict)
        assert isinstance(tool.output_schema, dict)


def test_call_tool_dispatches_handler() -> None:
    registry = ToolRegistry()
    registry.register(
        default_registry.get_tool("split_text")
    )

    result = registry.call_tool("split_text", text="abcdefghij", chunk_size=4, overlap=1)

    assert result == {"chunks": ["abcd", "defg", "ghij"]}
