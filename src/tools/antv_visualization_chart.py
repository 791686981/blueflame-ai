"""AntV visualization MCP tools via DashScope."""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "antv_visualization_chart"
ensure_tool_registered(_TOOL_NAME)


async def get_antv_visualization_chart_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_antv_visualization_chart_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


antv_visualization_chart: List[Any] = get_antv_visualization_chart_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_antv_visualization_chart_tools_async())
    print(f"获取到 {len(tools)} 个 AntV 可视化图表工具")
