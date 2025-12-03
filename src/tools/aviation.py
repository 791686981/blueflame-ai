"""Aviation MCP tools (飞常准) via DashScope."""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "aviation"
ensure_tool_registered(_TOOL_NAME)


async def get_aviation_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_aviation_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


aviation: List[Any] = get_aviation_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_aviation_tools_async())
    print(f"获取到 {len(tools)} 个 Aviation 工具")
