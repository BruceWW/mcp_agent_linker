# mcp-broker

**MCP server as Agent** — 用 MCP server 作为域 Agent 的完整定义载体，通过通用框架动态实例化，实现工具上下文隔离和零代码接入新领域。

## 背景

传统多工具 Agent 系统面临两个工程问题：

1. **工具上下文膨胀**：所有域的 tool 定义一次性注入主 Agent，50 个工具可能消耗 3-5 万 token，影响推理质量和成本。
2. **新域接入成本高**：每接入一个新领域，都需要修改框架代码。

## 核心思想

一个 MCP server 天然包含三类信息：

- **Prompts** — 定义 Agent 的角色和行为
- **Resources** — 提供领域知识和 Skills（约定 URI 格式 `skill:///<name>`）
- **Tools** — 暴露可执行的能力

因此，**一个 MCP server = 一个完整的域 Agent 定义**。本项目基于此构建通用框架：每个 MCP server 被封装为一个标准 LangChain Tool，主 Agent 按意图路由，子 Agent 工具上下文完全隔离。

```
接入新领域 = 新增一行 MCP 地址配置，不改框架代码
```

## 架构

```
[MCP-A地址, MCP-B地址, ...]
         │
         ▼ MCPTool.from_mcp()
[MCPTool-A, MCPTool-B, ...]   ← 标准 LangChain StructuredTool
         │
         ▼ create_agent(model, tools=...)
主 Agent（意图识别 + 路由）
         │ 调用对应 MCPTool
         ▼
MCPTool 内部：lazy 创建子 Agent
  └─ MCPLoader 拉取 prompt / tools / skills
  └─ create_agent 实例化子 Agent
         │
         ▼
子 Agent（工具上下文完全隔离）
  └─ 调用 MCP tools 执行任务 → 返回文本结果
```

**渐进式 Skill 披露**：子 Agent 启动时只注入 skill 目录（name + description），按需再加载具体内容，避免 prompt 膨胀。

## 安装

需要 Python 3.11+，使用 uv 管理依赖。

```bash
# 安装运行时依赖
uv sync

# 安装开发依赖（含 fastmcp，用于本地测试服务）
uv sync --extra dev
```

## 快速上手

### 方式一：MCPTool + 标准 create_agent（完全兼容 LangChain）

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from mcp_broker import MCPTool

model = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")

# 每个 MCP server 变成一个标准 LangChain Tool
tools = [
    MCPTool.from_mcp("http://food-mcp/mcp", model),
    MCPTool.from_mcp("http://calendar-mcp/mcp", model),
]

# 直接传给任意 LangChain agent
agent = create_agent(model, tools=tools)
result = agent.invoke({"messages": [HumanMessage(content="帮我点个午饭，30 块以内")]})
print(result["messages"][-1].content)
```

### 方式二：MCPAgentLinker 便捷封装

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from mcp_broker import MCPAgentLinker

model = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")

agent = MCPAgentLinker(
    model=model,
    mcp_urls=["http://food-mcp/mcp", "http://calendar-mcp/mcp"],
)
result = agent.invoke({"messages": [HumanMessage(content="帮我点个午饭，30 块以内")]})
print(result["messages"][-1].content)
```

### 方式三：手动加载 AgentDef（自定义集成）

```python
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from mcp_broker import MCPLoader

agent_def = MCPLoader("http://your-mcp-server/mcp").load()
# agent_def.system_prompt — MCP prompt 文本
# agent_def.tools         — LangChain BaseTool 列表
# agent_def.skills        — Skill 对象列表（来自 skill:/// resources）

skill_index = "\n".join(s.summary() for s in agent_def.skills)
system = agent_def.system_prompt + f"\n\n## 可用 Skills\n{skill_index}"

agent = create_agent(model, tools=agent_def.tools, system_prompt=system)
result = agent.invoke({"messages": [HumanMessage(content="帮我点个午饭，30 块以内")]})
```

## 开发

```bash
# 启动本地测试服务（外卖域 mock）
uv run python tests/food_agent_server.py

# 运行 MCPLoader 测试
uv run --extra dev python -m pytest tests/test_loader.py -v -s

# 运行端到端测试（需先启动 food_agent_server）
uv run --extra dev python -m pytest tests/test_agent.py -v -s
```

## 实现进度

- [x] 核心架构设计
- [x] `MCPLoader` — 从 MCP server 读取 prompt / tools / skills，返回 `AgentDef`
- [x] `MCPTool` — 将 MCP server 封装为标准 LangChain StructuredTool，完全兼容 `create_agent`
- [x] `MCPAgentLinker` — 便捷封装，传入 MCP 地址列表直接返回可执行 Agent
- [x] 渐进式 Skill 披露 — `Skill.summary()` 目录层 / `Skill.full_text()` 内容层
