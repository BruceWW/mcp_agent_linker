from pydantic import BaseModel, field_validator


class Skill(BaseModel):
    """单个 Skill 的数据对象，支持渐进式披露。

    渐进式披露策略：
    - 初始阶段：只向 agent 暴露 name + description（目录层）
    - 按需阶段：agent 请求具体 skill 时，再加载 content（内容层）
    """

    uri: str
    name: str
    description: str = ""
    content: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def extract_name_from_uri(cls, v: str) -> str:
        """若 name 未显式传入，从 uri 中提取（skill:///foo-bar -> foo-bar）"""
        return v

    @classmethod
    def from_uri(cls, uri: str, description: str = "", content: str | None = None) -> "Skill":
        name = uri.removeprefix("skill:///")
        return cls(uri=uri, name=name, description=description, content=content)

    def summary(self) -> str:
        """返回目录层摘要，用于初始注入 prompt。"""
        return f"- {self.name}: {self.description}" if self.description else f"- {self.name}"

    def full_text(self) -> str:
        """返回完整内容层，需要时再调用。"""
        if self.content is None:
            raise ValueError(f"Skill '{self.name}' content not loaded yet")
        return f"## {self.name}\n{self.content}"
