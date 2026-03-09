"""Step 2: ResourcesParser — 将 MCP resources 解析为可用的 skills"""


class ResourcesParser:
    def __init__(self, resources: list[dict]):
        self.resources = resources

    def parse(self) -> list[str]:
        """将 resources 解析为 skill 文本列表，供 agent 加载。

        约定：URI 格式 skill:///<skill-name> 的 resource 作为 skill。
        """
        raise NotImplementedError
