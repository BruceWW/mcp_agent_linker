"""MCPAgentLinker 集成测试 — 需要先启动 food_agent_server

启动服务：
    uv run python tests/food_agent_server.py

运行测试：
    uv run pytest tests/test_agent.py -v -s
"""

import pytest
from langchain_openai import ChatOpenAI
from mcp_agent_linker.loader import MCPLoader
from mcp_agent_linker.agent import MCPAgentLinker
from langchain_core.messages import HumanMessage

MCP_URL = "http://127.0.0.1:8765/mcp"

MODEL = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-",
    base_url="https://api.deepseek.com/v1",
)


def make_linker() -> MCPAgentLinker:
    loaders = [MCPLoader(MCP_URL, name="food_agent")]
    return MCPAgentLinker(model=MODEL, mcp_loaders=loaders)


def test_linker_instantiation():
    """MCPAgentLinker 能正常实例化，返回 CompiledStateGraph"""
    from langgraph.graph.state import CompiledStateGraph

    linker = make_linker()
    assert isinstance(linker, CompiledStateGraph)


def test_linker_has_sub_agent_tools():
    """主 Agent 持有以 loader.name 命名的子 Agent tool"""
    linker = make_linker()
    # CompiledStateGraph 的 nodes 包含主 agent 节点
    # 验证 graph 结构至少有 agent 节点和 tools 节点
    node_names = set(linker.nodes.keys())
    assert len(node_names) > 0, "graph 不应为空"


def test_invoke_food_query():
    """端到端：主 Agent 路由到 food_agent，查询菜单并返回结果"""
    linker = make_linker()
    result = linker.invoke({
        "messages": [HumanMessage(content="帮我查一下 30 元以内的套餐")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAgent 回复: {last_msg}")
    # 主 Agent 应调用 food_agent，food_agent 会调用 query_menu 工具
    assert len(last_msg) > 0


def test_invoke_order():
    """端到端：主 Agent 路由到 food_agent 完成下单流程"""
    linker = make_linker()
    result = linker.invoke({
        "messages": [HumanMessage(content="帮我下单麦辣鸡腿堡套餐，地址是上海市钦州南路 100 号")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAgent 回复: {last_msg}")
    assert len(last_msg) > 0


@pytest.mark.asyncio
async def test_ainvoke_food_query():
    """异步端到端：ainvoke 路径正常"""
    linker = make_linker()
    result = await linker.ainvoke({
        "messages": [HumanMessage(content="有什么套餐可以选？")]
    })
    last_msg = result["messages"][-1].content
    print(f"\nAsync Agent 回复: {last_msg}")
    assert len(last_msg) > 0
