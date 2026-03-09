from pydantic import BaseModel, ConfigDict
from langchain_core.tools import BaseTool
from .skill import Skill


class AgentDef(BaseModel):
    """MCPLoader.load() 的返回对象，字段对齐 LangChain agent 创建入参。

    渐进式披露用法：
        agent_def = MCPLoader(url).load()

        # 初始 prompt 只注入 skill 目录（name + description）
        skill_index = "\\n".join(s.summary() for s in agent_def.skills)

        # agent 请求具体 skill 时再展开 content
        skill_content = agent_def.skill("ordering-guide").full_text()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 对应 create_react_agent(llm, tools, prompt) 的 tools 入参
    tools: list[BaseTool]

    # 对应 SystemMessage 的文本内容，调用方包装成 ChatPromptTemplate
    system_prompt: str

    # MCP resources 中 skill:/// 前缀的资源，支持渐进式披露
    skills: list[Skill]

    def skill(self, name: str) -> Skill:
        """按名称查找 skill，供 agent 按需加载 content。"""
        for s in self.skills:
            if s.name == name:
                return s
        raise KeyError(f"Skill '{name}' not found")
