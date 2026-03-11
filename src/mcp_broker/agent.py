"""MCPAgentLinker — MCPTool 列表 + create_agent 的便捷封装

用法:
    agent = MCPAgentLinker(model=model, mcp_urls=["http://food-mcp/mcp"])
    result = agent.invoke({"messages": [HumanMessage(content="帮我点个午饭")]})

直接用 MCPTool 组合更灵活:
    tools = [MCPTool.from_mcp("http://food-mcp/mcp", model)]
    agent = create_agent(model, tools=tools)
"""

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from mcp_broker.tool import MCPTool


def MCPAgentLinker(
    model: str | BaseChatModel,
    mcp_urls: list[str],
    **kwargs,
) -> CompiledStateGraph:
    """传入 MCP 地址列表，返回可直接调用的 LangGraph agent。

    Args:
        model: LangChain 模型实例或模型字符串（如 "openai:gpt-4o"）
        mcp_urls: MCP server 地址列表
        **kwargs: 透传给 create_agent 的额外参数
    """
    tools = [MCPTool.from_mcp(url, model) for url in mcp_urls]
    return create_agent(model, tools=tools, **kwargs)
