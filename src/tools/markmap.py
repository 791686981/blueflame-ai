"""Markmap 思维导图 MCP 工具（ModelScope streamable_http）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "markmap"
ensure_tool_registered(_TOOL_NAME)


async def get_markmap_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_markmap_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


markmap: List[Any] = get_markmap_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_markmap_tools_async())
    print(f"获取到 {len(tools)} 个 Markmap 思维导图工具")
