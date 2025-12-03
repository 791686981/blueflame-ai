"""12306 火车票查询 MCP 工具（DashScope SSE）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "railway_12306"
ensure_tool_registered(_TOOL_NAME)


async def get_railway_12306_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_railway_12306_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


railway_12306: List[Any] = get_railway_12306_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_railway_12306_tools_async())
    print(f"获取到 {len(tools)} 个 12306 车票查询工具")
