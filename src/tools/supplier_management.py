"""供应商管理 MCP 工具（DashScope streamable_http）。"""

from typing import Any, List

from .registry import ensure_tool_registered, get_tools, get_tools_async

_TOOL_NAME = "supplier_management"
ensure_tool_registered(_TOOL_NAME)


async def get_supplier_management_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_supplier_management_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


supplier_management: List[Any] = get_supplier_management_tools()


if __name__ == "__main__":
    import asyncio

    tools = asyncio.run(get_supplier_management_tools_async())
    print(f"获取到 {len(tools)} 个 供应商管理 工具")
