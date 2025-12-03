"""通达信软件 MCP 工具（DashScope SSE）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "tendency_software"
ensure_tool_registered(_TOOL_NAME)


async def get_tendency_software_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_tendency_software_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


tendency_software: List[Any] = get_tendency_software_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_tendency_software_tools_async())
    print(f"获取到 {len(tools)} 个 通达信 工具")
