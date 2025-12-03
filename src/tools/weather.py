"""Weather MCP tools powered by the shared tool registry."""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "weather"
ensure_tool_registered(_TOOL_NAME)


async def get_weather_tools_async(*, refresh: bool = False) -> List[Any]:
    """Async helper that returns the latest Weather tools."""
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_weather_tools(*, refresh: bool = False) -> List[Any]:
    """Sync helper for environments without an event loop."""
    return get_tools(_TOOL_NAME, refresh=refresh)


weather: List[Any] = get_weather_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_weather_tools_async())
    print(f"获取到 {len(tools)} 个 Weather 工具")
