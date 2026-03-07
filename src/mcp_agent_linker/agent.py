"""MCPAgentLinker — 继承 LangChain CompiledStateGraph 的主 Agent

初始化时从每个 MCPLoader 的 get_content() 构建子 Agent 选项，
由主 Agent 的 LLM 根据用户意图路由到对应子 Agent。
"""

import asyncio
import concurrent.futures
from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain.agents import create_agent, AgentState
from langgraph.graph.state import CompiledStateGraph

from mcp_agent_linker.loader import MCPLoader


class _TaskInput(BaseModel):
    task: str = Field(description="要委托给子 Agent 的具体任务描述")


class MCPAgentLinker(CompiledStateGraph):
    """基于 MCP server 列表的主 Agent。

    启动时对每个 MCPLoader 调用 get_content()，将返回的 prompt
    作为对应子 Agent tool 的 description，供主 Agent LLM 做意图路由。

    用法:
        loaders = [
            MCPLoader("http://food-mcp/mcp", name="food_agent"),
            MCPLoader("http://calendar-mcp/mcp", name="calendar_agent"),
        ]
        agent = MCPAgentLinker(model="anthropic:claude-sonnet-4-6", mcp_loaders=loaders)
        result = agent.invoke({"messages": [{"role": "user", "content": "帮我点个午饭"}]})
        print(result["messages"][-1].content)
    """

    def __new__(
        cls,
        model: str | BaseChatModel,
        mcp_loaders: list[MCPLoader],
        **kwargs: Any,
    ) -> "MCPAgentLinker":
        tools = [cls._make_sub_agent_tool(loader, model) for loader in mcp_loaders]

        agent_descriptions = "\n".join(
            f"- {t.name}: {t.description}" for t in tools
        )
        system_prompt = (
            "你是一个主控 Agent，负责理解用户意图并路由到合适的子 Agent 执行任务。\n\n"
            f"可用子 Agent：\n{agent_descriptions}\n\n"
            "分析用户请求后，调用对应的子 Agent tool，并将其返回结果直接呈现给用户。"
        )

        graph = create_agent(model, tools=tools, system_prompt=system_prompt, **kwargs)
        # 将 graph 实例的类替换为 MCPAgentLinker，保留全部图结构
        graph.__class__ = cls
        return graph  # type: ignore[return-value]

    @staticmethod
    def _make_sub_agent_tool(loader: MCPLoader, model: str | BaseChatModel) -> StructuredTool:
        content = loader.get_content()

        def _run(task: str) -> str:
            agent_def = loader.load()
            system = agent_def.system_prompt
            if agent_def.skills:
                skill_index = "\n".join(s.summary() for s in agent_def.skills)
                system += f"\n\n## 可用 Skills\n{skill_index}"
            sub = create_agent(model, tools=agent_def.tools, system_prompt=system)
            result = sub.invoke({"messages": [HumanMessage(content=task)]})
            return result["messages"][-1].content

        async def _arun(task: str) -> str:
            agent_def = await loader.load_async()
            system = agent_def.system_prompt
            if agent_def.skills:
                skill_index = "\n".join(s.summary() for s in agent_def.skills)
                system += f"\n\n## 可用 Skills\n{skill_index}"
            sub = create_agent(model, tools=agent_def.tools, system_prompt=system)
            result = await sub.ainvoke({"messages": [HumanMessage(content=task)]})
            return result["messages"][-1].content

        return StructuredTool.from_function(
            func=_run,
            coroutine=_arun,
            name=loader.name,
            description=content,
            args_schema=_TaskInput,
        )
