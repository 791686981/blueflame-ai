"""企业风险查询 MCP 工具（DashScope streamable_http）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "enterprise_risk"
ensure_tool_registered(_TOOL_NAME)


async def get_enterprise_risk_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_enterprise_risk_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


enterprise_risk: List[Any] = get_enterprise_risk_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_enterprise_risk_tools_async())
    print(f"获取到 {len(tools)} 个 企业风险查询 工具")
