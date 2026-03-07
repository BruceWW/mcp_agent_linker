"""MCPLoader 集成测试 — 需要先启动 mcp_test_server"""

import pytest
from mcp_agent_linker.loader import MCPLoader, AgentDef

MCP_URL = "http://127.0.0.1:8765/mcp"


def test_load_returns_agent_def():
    loader = MCPLoader(MCP_URL)
    result = loader.load()

    assert isinstance(result, AgentDef)


def test_system_prompt():
    loader = MCPLoader(MCP_URL)
    result = loader.load()

    assert len(result.system_prompt) > 0
    print(f"\nsystem_prompt: {result.system_prompt}")


def test_tools():
    loader = MCPLoader(MCP_URL)
    result = loader.load()

    assert len(result.tools) == 2
    tool_names = {t.name for t in result.tools}
    assert tool_names == {"query_menu", "create_order"}
    print(f"\ntools: {tool_names}")


def test_skills():
    loader = MCPLoader(MCP_URL)
    result = loader.load()

    assert len(result.skills) == 2
    skill = result.skills[0]
    print(f"\nskill name: {skill.name}")
    print(f"skill summary: {skill.summary()}")
    print(f"skill content: {skill.content[:50]}...")


def test_get_content():
    loader = MCPLoader(MCP_URL)
    content = loader.get_content()

    assert len(content) > 0
    print(f"\nget_content: {content}")


def test_tool_call():
    loader = MCPLoader(MCP_URL)
    result = loader.load()

    query_menu = next(t for t in result.tools if t.name == "query_menu")
    output = query_menu.invoke({"max_price": 30.0})
    print(f"\ntool call result: {output}")
    assert "麦辣鸡腿堡" in output
