"""Amap Maps MCP tools (stdio) managed by ToolManager."""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "amap_maps"
ensure_tool_registered(_TOOL_NAME)


async def get_amap_maps_tools_async(*, refresh: bool = False) -> List[Any]:
    """Async helper returning the High De map tools."""
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_amap_maps_tools(*, refresh: bool = False) -> List[Any]:
    """Sync helper returning cached Amap tools."""
    return get_tools(_TOOL_NAME, refresh=refresh)


amap_maps: List[Any] = get_amap_maps_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_amap_maps_tools_async())
    print(f"获取到 {len(tools)} 个高德地图工具")
