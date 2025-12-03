# Blueflame AI Tooling

This repository now ships with a shared tool framework that treats MCP servers and in-process Python tools the same way. Agents only need to `import src.tools.<name>` and the registry takes care of bringing the correct tool list online (stdio MCP, DashScope SSE, or custom callables).

## Architecture

- `src/tools/tool_manager.py` exposes `ToolManager`, `ToolProvider` subclasses, caching, and thread-safe async helpers (`get_tools`/`get_tools_async`).
- `src/tools/registry.py` describes every built-in tool declaratively via `DashScopeMCPSpec` or `StdIOMCPSpec`. The registry registers specs lazily and exports helpers:
  - `ensure_tool_registered(name)` – idempotently register the provider before loading tools.
  - `get_tools` / `get_tools_async` – wrap the manager and guarantee the spec exists.
  - `register_callable_tool` – drop in any custom LangChain tools built in Python.
- Individual modules (e.g. `src/tools/weather.py`) are now skinny wrappers: they ensure registration, expose sync/async getters, and keep the old module-level list (`weather`, `web_search`, etc.) for backwards compatibility.

## Adding A DashScope MCP Tool

1. Open `src/tools/registry.py` and add a new `DashScopeMCPSpec` entry:

   ```python
   register_spec(
       DashScopeMCPSpec(
           "my_tool",
           server_name="market-xxxx",
           transport="sse",  # or "streamable_http"
           description="一句话介绍",
           tags=("category", "keyword"),
       )
   )
   ```
2. Create a `src/tools/my_tool.py` wrapper identical to the existing ones (import `ensure_tool_registered`, expose sync/async getters, and export the module-level list).
3. Import `my_tool` wherever needed: `from src.tools.my_tool import my_tool`.

The registry automatically handles DashScope authentication via `settings.dashscope_api_key`. Missing keys disable the provider without raising, so agents can still boot.

## Adding A stdio MCP Tool

Use `StdIOMCPSpec` when the MCP server is spawned locally:

```python
register_spec(
    StdIOMCPSpec(
        "custom_stdio",
        server_name="custom",
        command="node",
        args=("path/to/server.js",),
        env_factory=lambda: {"MY_KEY": settings.custom_key} if settings.custom_key else None,
        description="本地工具",
        tags=("local",),
    )
)
```

If the `env_factory` returns `None`, the tool stays disabled (useful when credentials are optional).

## Registering Pure Python Tools

When a tool is implemented directly in Python/LangChain (no MCP), register it in code:

```python
from src.tools.registry import register_callable_tool
from langchain_core.tools import tool

@tool
def hello(name: str) -> str:
    return f"Hello {name}!"

register_callable_tool(
    "hello_world",
    builder=lambda: [hello],
    description="示例 Python 工具",
    tags=("demo",),
)
```

The callable can be sync or async. The registry wires it into `ToolManager`, so the same `ensure_tool_registered` / `get_tools` helpers work.

## Cache & Refresh

Each provider can set `cache_ttl` (seconds). By default tools are cached indefinitely until you call:

- `tool_manager.get_tools(name, refresh=True)` or
- module helpers such as `get_weather_tools(refresh=True)`

This forces a new MCP handshake when remote capabilities change.
