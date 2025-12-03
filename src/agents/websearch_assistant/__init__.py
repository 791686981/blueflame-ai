"""
Template Agent
简洁、可复制的 LangGraph 代理模板（含常用“中间件”能力）。

惰性导入以避免在包导入阶段进行重量级初始化。
"""

from typing import TYPE_CHECKING

__all__ = [
    "create_agent",
    "graph",
    "TemplateAgentConfig",
]

if TYPE_CHECKING:
    # 仅类型检查时导入真实实现
    from .agent import create_agent, graph, TemplateAgentConfig  # noqa: F401


def __getattr__(name: str):
    if name in {"create_agent", "graph", "TemplateAgentConfig"}:
        from .agent import create_agent, graph, TemplateAgentConfig  # type: ignore

        if name == "create_agent":
            return create_agent
        if name == "graph":
            return graph
        return TemplateAgentConfig
    raise AttributeError(f"module 'agent_service.agents.template_agent' has no attribute {name!r}")

