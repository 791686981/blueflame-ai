"""美食侦探 MCP 工具（DashScope streamable_http）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "gourmet_guide"
ensure_tool_registered(_TOOL_NAME)


async def get_gourmet_guide_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_gourmet_guide_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


gourmet_guide: List[Any] = get_gourmet_guide_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_gourmet_guide_tools_async())
    print(f"获取到 {len(tools)} 个 美食侦探 工具")
