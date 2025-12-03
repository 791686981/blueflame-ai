"""Declarative registry for MCP/custom tools built on top of ToolManager."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Sequence

from ..common.config import settings
from .tool_manager import (
    CallableToolProvider,
    MCPToolProvider,
    ToolManagerError,
    ToolProvider,
    tool_manager,
)


class ToolSpec(ABC):
    """Declarative description that knows how to produce a ToolProvider."""

    def __init__(
        self,
        tool_name: str,
        *,
        description: str = "",
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.description = description
        self.tags = tuple(tags or ())
        self.cache_ttl = cache_ttl

    @abstractmethod
    def build_provider(self) -> ToolProvider:
        ...


class DashScopeMCPSpec(ToolSpec):
    """MCP spec for DashScope hosted servers (SSE or streamable_http)."""

    def __init__(
        self,
        tool_name: str,
        *,
        server_name: str,
        transport: str = "sse",
        description: str = "",
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        super().__init__(tool_name, description=description, tags=tags, cache_ttl=cache_ttl)
        self.server_name = server_name
        self.transport = transport

    def build_provider(self) -> MCPToolProvider:
        def _servers() -> Mapping[str, Any] | None:
            api_key = settings.dashscope_api_key
            if not api_key:
                return None
            suffix = "sse" if self.transport == "sse" else "mcp"
            return {
                self.server_name: {
                    "transport": self.transport,
                    "url": f"https://dashscope.aliyuncs.com/api/v1/mcps/{self.server_name}/{suffix}",
                    "headers": {
                        "Authorization": f"Bearer {api_key}",
                    },
                }
            }

        tags = ("dashscope", "mcp", self.transport) + self.tags
        return MCPToolProvider(
            name=self.tool_name,
            servers=_servers,
            description=self.description,
            tags=tags,
            cache_ttl=self.cache_ttl,
        )


class StdIOMCPSpec(ToolSpec):
    """Spec for MCP servers launched locally via stdio."""

    def __init__(
        self,
        tool_name: str,
        *,
        server_name: str,
        command: str,
        args: Sequence[str] = (),
        env_factory: Callable[[], Mapping[str, str] | None] | None = None,
        description: str = "",
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        super().__init__(tool_name, description=description, tags=tags, cache_ttl=cache_ttl)
        self.server_name = server_name
        self.command = command
        self.args = tuple(args)
        self.env_factory = env_factory or (lambda: {})

    def build_provider(self) -> MCPToolProvider:
        def _servers() -> Mapping[str, Any] | None:
            env = self.env_factory()
            if env is None:
                return None
            return {
                self.server_name: {
                    "transport": "stdio",
                    "command": self.command,
                    "args": list(self.args),
                    "env": env,
                }
            }

        tags = ("stdio", "mcp") + self.tags
        return MCPToolProvider(
            name=self.tool_name,
            servers=_servers,
            description=self.description,
            tags=tags,
            cache_ttl=self.cache_ttl,
        )


class StaticMCPSpec(ToolSpec):
    """Spec for externally hosted MCP servers with static config."""

    def __init__(
        self,
        tool_name: str,
        *,
        server_name: str,
        transport: str = "streamable_http",
        url: str,
        headers: Mapping[str, str] | None = None,
        extra_config: Mapping[str, Any] | None = None,
        description: str = "",
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        super().__init__(tool_name, description=description, tags=tags, cache_ttl=cache_ttl)
        self.server_name = server_name
        self.transport = transport
        self.url = url
        self.headers = dict(headers or {})
        self.extra_config = dict(extra_config or {})

    def build_provider(self) -> MCPToolProvider:
        server_cfg: Dict[str, Any] = {
            "transport": self.transport,
            "url": self.url,
        }
        if self.headers:
            server_cfg["headers"] = dict(self.headers)
        server_cfg.update(self.extra_config)

        return MCPToolProvider(
            name=self.tool_name,
            servers={self.server_name: server_cfg},
            description=self.description,
            tags=("mcp", self.transport) + self.tags,
            cache_ttl=self.cache_ttl,
        )


_TOOL_SPECS: Dict[str, ToolSpec] = {}


def register_spec(spec: ToolSpec, *, override: bool = False) -> None:
    if spec.tool_name in _TOOL_SPECS and not override:
        raise ToolManagerError(f"Tool spec '{spec.tool_name}' already registered")
    _TOOL_SPECS[spec.tool_name] = spec


def register_callable_tool(
    name: str,
    builder: Callable[[], Sequence[Any]] | Callable[[], Awaitable[Sequence[Any]]],
    *,
    description: str = "",
    tags: Sequence[str] | None = None,
    cache_ttl: float | None = None,
    override: bool = False,
) -> None:
    """Register adhoc Python tools without going through a spec."""

    provider = CallableToolProvider(
        name,
        builder,
        description=description,
        tags=tags,
        cache_ttl=cache_ttl,
    )
    tool_manager.register_provider(provider, override=override)


def ensure_tool_registered(name: str) -> None:
    if tool_manager.is_registered(name):
        return
    spec = _TOOL_SPECS.get(name)
    if not spec:
        raise ToolManagerError(f"No tool spec registered for '{name}'")
    provider = spec.build_provider()
    tool_manager.register_provider(provider)


def list_specs() -> List[str]:
    return sorted(_TOOL_SPECS.keys())


def get_tools(name: str, *, refresh: bool = False) -> List[Any]:
    ensure_tool_registered(name)
    return tool_manager.get_tools(name, refresh=refresh)


def get_tools_async(name: str, *, refresh: bool = False):  # -> Awaitable[List[Any]]
    ensure_tool_registered(name)
    return tool_manager.get_tools_async(name, refresh=refresh)


# Register built-in MCP specs --------------------------------------------------

register_spec(
    StdIOMCPSpec(
        "amap_maps",
        server_name="amap-maps",
        command="npx",
        args=("-y", "@amap/amap-maps-mcp-server"),
        env_factory=lambda: (
            {"AMAP_MAPS_API_KEY": settings.amap_maps_api_key}
            if settings.amap_maps_api_key
            else None
        ),
        description="高德地图 stdio MCP server",
        tags=("geospatial", "maps"),
    )
)

register_spec(
    StdIOMCPSpec(
        "antv_visualization_chart",
        server_name="mcp-server-chart",
        command="npx",
        args=("-y", "@antv/mcp-server-chart"),
        description="AntV 官方 MCP 图表生成服务（npx @antv/mcp-server-chart）",
        tags=("visualization", "antv"),
    )
)

register_spec(
    DashScopeMCPSpec(
        "aviation",
        server_name="Aviation",
        description="飞常准航班信息",
        tags=("transport", "flight"),
    )
)

register_spec(
    DashScopeMCPSpec(
        "bidding_full",
        server_name="market-cmapi00066410",
        transport="streamable_http",
        description="招投标全量数据",
        tags=("bidding",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "bidding_tenders",
        server_name="market-cmapi00071999",
        transport="streamable_http",
        description="水滴信用招投标",
        tags=("bidding",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "enterprise_bigdata",
        server_name="market-cmapi00071990",
        transport="streamable_http",
        description="企业大数据查询",
        tags=("enterprise",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "enterprise_registry",
        server_name="market-cmapi029030",
        transport="streamable_http",
        description="企业工商注册信息",
        tags=("enterprise", "registry"),
    )
)

register_spec(
    DashScopeMCPSpec(
        "enterprise_risk",
        server_name="market-cmapi00071991",
        transport="streamable_http",
        description="企业风险洞察",
        tags=("enterprise", "risk"),
    )
)

register_spec(
    DashScopeMCPSpec(
        "gourmet_guide",
        server_name="market-cmapi00067124",
        transport="streamable_http",
        description="美食侦探推荐",
        tags=("lifestyle",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "railway_12306",
        server_name="china-railway",
        description="12306 车票查询",
        tags=("transport", "railway"),
    )
)

register_spec(
    DashScopeMCPSpec(
        "supplier_management",
        server_name="market-cmapi00071992",
        transport="streamable_http",
        description="供应商管理",
        tags=("supply-chain",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "tendency_software",
        server_name="tendency-software",
        description="通达信软件工具",
        tags=("finance",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "time_tools",
        server_name="TimeZone",
        description="TimeZone 时区工具",
        tags=("time",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "weather",
        server_name="weather",
        description="实时天气",
        tags=("weather",),
    )
)

register_spec(
    DashScopeMCPSpec(
        "web_search",
        server_name="WebSearch",
        description="DashScope WebSearch",
        tags=("search",),
    )
)

register_spec(
    StdIOMCPSpec(
        "markmap",
        server_name="Markmap",
        command="npx",
        args=("-y", "@jinzcdev/markmap-mcp-server"),
        env_factory=lambda: {"MARKMAP_DIR": str(Path.home() / "Downloads")},
        description="本地 npx 启动的 Markmap 思维导图 MCP 服务（输出至 Downloads）",
        tags=("mindmap", "knowledge"),
    )
)
