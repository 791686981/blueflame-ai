"""TimeZone MCP 工具（DashScope SSE）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "time_tools"
ensure_tool_registered(_TOOL_NAME)


async def get_time_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_time_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


time_tools: List[Any] = get_time_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_time_tools_async())
    print(f"获取到 {len(tools)} 个时间/时区转换工具")
