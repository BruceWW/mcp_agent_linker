"""MCPAgentLinker 集成测试 — 需要先启动 food_agent_server

启动服务：
    uv run python tests/food_agent_server.py

运行测试：
    uv run pytest tests/test_agent.py -v -s
"""

import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from mcp_broker import MCPTool, MCPAgentLinker

MCP_URL = "http://127.0.0.1:8765/mcp"

MODEL = ChatOpenAI(
    model="deepseek-chat",
    api_key="",
    base_url="https://api.deepseek.com/v1",
)


# ── MCPTool 测试 ──────────────────────────────────────────────

def test_mcp_tool_instantiation():
    """MCPTool.from_mcp 能正常创建，description 来自 MCP init prompt"""
    tool = MCPTool.from_mcp(MCP_URL, MODEL, name="food_agent")
    assert tool.name == "food_agent"
    assert len(tool.description) > 0
    print(f"\ntool.description: {tool.description}")


def test_mcp_tool_invoke():
    """MCPTool 被调用时创建子 agent 并返回结果"""
    tool = MCPTool.from_mcp(MCP_URL, MODEL, name="food_agent")
    result = tool.invoke({"task": "查一下 30 元以内的套餐"})
    print(f"\ntool result: {result}")
    assert len(result) > 0


def test_mcp_tool_with_standard_create_agent():
    """MCPTool 直接传给标准 create_agent，端到端正常"""
    from langchain.agents import create_agent

    tools = [MCPTool.from_mcp(MCP_URL, MODEL, name="food_agent")]
    agent = create_agent(MODEL, tools=tools)

    assert isinstance(agent, CompiledStateGraph)
    result = agent.invoke({"messages": [HumanMessage(content="有什么套餐？")]})
    last_msg = result["messages"][-1].content
    print(f"\nAgent 回复: {last_msg}")
    assert len(last_msg) > 0


# ── MCPAgentLinker 测试 ───────────────────────────────────────

def test_linker_instantiation():
    """MCPAgentLinker 返回标准 CompiledStateGraph"""
    agent = MCPAgentLinker(model=MODEL, mcp_urls=[MCP_URL])
    assert isinstance(agent, CompiledStateGraph)


def test_linker_invoke_food_query():
    """端到端：主 Agent 路由到 food_agent 查询菜单"""
    agent = MCPAgentLinker(model=MODEL, mcp_urls=[MCP_URL])
    result = agent.invoke({
        "messages": [HumanMessage(content="帮我查一下 30 元以内的套餐")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAgent 回复: {last_msg}")
    assert len(last_msg) > 0


def test_linker_invoke_order():
    """端到端：主 Agent 路由到 food_agent 完成下单"""
    agent = MCPAgentLinker(model=MODEL, mcp_urls=[MCP_URL])
    result = agent.invoke({
        "messages": [HumanMessage(content="帮我下单麦辣鸡腿堡套餐，地址是上海市钦州南路 100 号")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAgent 回复: {last_msg}")
    assert len(last_msg) > 0


@pytest.mark.asyncio
async def test_linker_ainvoke():
    """异步端到端：ainvoke 路径正常"""
    agent = MCPAgentLinker(model=MODEL, mcp_urls=[MCP_URL])
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="有什么套餐可以选？")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAsync Agent 回复: {last_msg}")
    assert len(last_msg) > 0
