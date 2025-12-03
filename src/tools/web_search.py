"""DashScope WebSearch MCP 工具."""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "web_search"
ensure_tool_registered(_TOOL_NAME)


async def get_web_search_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_web_search_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


web_search: List[Any] = get_web_search_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_web_search_tools_async())
    print(f"获取到 {len(tools)} 个 WebSearch 工具")
