"""MCPTool — 将单个 MCP server 封装为标准 LangChain StructuredTool

用法:
    from mcp_broker import MCPTool
    from langchain.agents import create_agent

    tools = [MCPTool("http://food-mcp/mcp"), MCPTool("http://calendar-mcp/mcp")]
    agent = create_agent(model, tools=tools)
"""

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool

from mcp_broker.loader import MCPLoader
from mcp_broker.models import TaskInput


class MCPTool(StructuredTool):
    """将一个 MCP server 封装为可被 LangChain agent 调用的 tool。

    初始化时从 MCP server 拉取 init prompt 作为 tool description，
    供主 agent 做意图路由；被调用时 lazy 创建子 agent 执行任务。
    """

    @classmethod
    def from_mcp(
        cls,
        mcp_url: str,
        model: str | BaseChatModel,
        name: str | None = None,
        prompt_name: str = "init",
    ) -> "MCPTool":
        loader = MCPLoader(mcp_url, prompt_name=prompt_name, name=name)
        description = loader.get_content()

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

        return cls.from_function(
            func=_run,
            coroutine=_arun,
            name=loader.name,
            description=description,
            args_schema=TaskInput,
        )
