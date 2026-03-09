"""Step 1: MCPLoader — 读取 MCP server，解析 prompt / resources / tools"""

import asyncio
import concurrent.futures
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pydantic import create_model as pydantic_create_model
from langchain_core.tools import BaseTool, StructuredTool
from mcp_broker.models import AgentDef, Skill


class MCPLoader:
    def __init__(self, mcp_url: str, prompt_name: str = "init", name: str | None = None):
        self.mcp_url = mcp_url
        self.prompt_name = prompt_name
        self.name = name or _name_from_url(mcp_url)

    def load(self) -> AgentDef:
        """同步加载，内部启动独立线程运行 event loop，兼容已有 loop 的环境。"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, self._load_async())
            return future.result()

    async def load_async(self) -> AgentDef:
        return await self._load_async()

    def get_content(self) -> str:
        """获取 prompt_name 对应的 prompt 内容，供主 Agent 做子 Agent 选择。"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, self._get_content_async())
            return future.result()

    async def get_content_async(self) -> str:
        return await self._get_content_async()

    async def _get_content_async(self) -> str:
        async with streamable_http_client(self.mcp_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await self._fetch_prompt(session)

    async def _load_async(self) -> AgentDef:
        async with streamable_http_client(self.mcp_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                system_prompt = await self._fetch_prompt(session)
                tools = await self._fetch_tools(session)
                skills = await self._fetch_skills(session)

        return AgentDef(system_prompt=system_prompt, tools=tools, skills=skills)

    async def _fetch_prompt(self, session: ClientSession) -> str:
        result = await session.get_prompt(self.prompt_name)
        texts = [
            msg.content.text
            for msg in result.messages
            if hasattr(msg.content, "text")
        ]
        return "\n".join(texts)

    async def _fetch_tools(self, session: ClientSession) -> list[BaseTool]:
        result = await session.list_tools()
        return [self._make_tool(t) for t in result.tools]

    def _make_tool(self, tool_def) -> StructuredTool:
        mcp_url = self.mcp_url
        tool_name = tool_def.name

        async def _acall(**kwargs: Any) -> str:
            async with streamable_http_client(mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, kwargs)
                    return result.content[0].text if result.content else ""

        def _call(**kwargs: Any) -> str:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _acall(**kwargs))
                return future.result()

        args_schema = _build_args_schema(tool_name, tool_def.inputSchema or {})

        return StructuredTool.from_function(
            func=_call,
            coroutine=_acall,
            name=tool_name,
            description=tool_def.description or "",
            args_schema=args_schema,
        )

    async def _fetch_skills(self, session: ClientSession) -> list[Skill]:
        result = await session.list_resources()
        skills = []
        for resource in result.resources:
            uri = str(resource.uri)
            if not uri.startswith("skill:///"):
                continue
            content_result = await session.read_resource(uri)
            content = next(
                (c.text for c in content_result.contents if hasattr(c, "text")),
                None,
            )
            skills.append(Skill.from_uri(
                uri=uri,
                description=resource.description or "",
                content=content,
            ))
        return skills


def _name_from_url(url: str) -> str:
    """从 MCP URL 提取可用作 tool name 的标识符。"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname or "agent"
    port = f"_{parsed.port}" if parsed.port else ""
    name = f"{host}{port}".replace(".", "_").replace("-", "_")
    # 确保首字符是字母
    if name and name[0].isdigit():
        name = f"agent_{name}"
    return name


def _build_args_schema(tool_name: str, json_schema: dict):
    properties = json_schema.get("properties", {})
    required = set(json_schema.get("required", []))

    if not properties:
        return None

    _TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    fields = {}
    for name, schema in properties.items():
        py_type = _TYPE_MAP.get(schema.get("type", "string"), str)
        default = ... if name in required else None
        fields[name] = (py_type, default)

    return pydantic_create_model(f"{tool_name}_args", **fields)
