# mcp-agent-linker

**MCP server as Agent** — 用 MCP server 作为域 Agent 的完整定义载体，通过通用插件动态实例化，实现工具上下文隔离和零代码接入新领域。

## 背景

传统多工具 Agent 系统面临两个工程问题：

1. **工具上下文膨胀**：所有域的 tool 定义一次性注入主 Agent，50 个工具可能消耗 3-5 万 token，影响推理质量和成本。
2. **新域接入成本高**：每接入一个新领域，都需要修改框架代码。

## 核心思想

一个 MCP server 天然包含三类信息：

- **Prompts** — 定义 Agent 的角色和行为
- **Resources** — 提供领域知识和 Skills（约定 URI 格式 `skill:///<name>`）
- **Tools** — 暴露可执行的能力

因此，**一个 MCP server = 一个完整的域 Agent 定义**。本项目基于此构建通用框架：配置 MCP 地址列表，插件自动实例化对应的域 Agent，子 Agent 工具上下文完全隔离。

```
接入新领域 = 新增一行 MCP 地址配置，不改框架代码
```

## 架构

```
配置层: [MCP-A地址, MCP-B地址, ...]
         │
         ▼
主 Agent（意图识别 + 编排）
         │ 识别到目标域
         ▼
Plugin（子 Agent 工厂）
  └─ MCPLoader: 读取 prompt / resources / tools
  └─ ResourcesParser: 解析 skills
  └─ 实例化 LangChain Agent
         │
         ▼
子 Agent（工具上下文完全隔离）
  └─ 执行完毕 → 返回文本结果给主 Agent
```

## 安装

需要 Python 3.11+，使用 uv 管理依赖。

```bash
# 安装运行时依赖
uv sync

# 安装开发依赖（含 fastmcp，用于本地测试服务）
uv sync --extra dev
```

## 快速上手

```python
from mcp_agent_linker import MCPLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_react_agent, AgentExecutor

# 从 MCP server 加载域 Agent 定义
agent_def = MCPLoader("http://your-mcp-server/mcp").load()

# agent_def.system_prompt — MCP prompt 文本
# agent_def.tools         — LangChain BaseTool 列表
# agent_def.skills        — skill 文本列表（来自 skill:/// resources）

system = agent_def.system_prompt + "\n\n" + "\n\n".join(agent_def.skills)
prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_react_agent(llm, agent_def.tools, prompt)
executor = AgentExecutor(agent=agent, tools=agent_def.tools)
executor.invoke({"input": "帮我点个午饭，30 块以内"})
```

## 开发

```bash
# 启动本地测试服务（外卖域 mock）
uv run python tests/food_agent_server.py

# 运行测试
uv run pytest tests/ -v -s
```

## 实现进度

- [x] 核心架构设计
- [x] `MCPLoader` — 读取 MCP server，返回 `AgentDef`（prompt / tools / skills）
- [ ] `ResourcesParser` — 扩展 skill 解析逻辑
- [ ] `MCPAgentLinker` — 主封装类，传入 MCP 地址直接创建可执行 Agent
- [ ] 主 Agent 编排层（意图识别 + 多域协作）
