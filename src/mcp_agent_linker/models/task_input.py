from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    task: str = Field(description="要委托给子 Agent 的具体任务描述")
