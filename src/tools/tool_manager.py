"""Central management utilities for MCP and custom LangChain tools."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional, Sequence
from weakref import WeakKeyDictionary

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


class ToolManagerError(RuntimeError):
    """Raised when the tool registry is misconfigured or invoked incorrectly."""


class ToolProvider(ABC):
    """Base abstraction for anything that can build a list of LangChain tools."""

    kind: str = "custom"

    def __init__(
        self,
        name: str,
        *,
        description: str | None = None,
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        self.name = name
        self.description = description or ""
        self.tags = tuple(tags or ())
        self.cache_ttl = cache_ttl

    @abstractmethod
    async def _load(self) -> Sequence[Any]:
        """Execute the actual loading logic and return the raw tools."""

    async def load(self) -> List[Any]:
        tools = await self._load()
        return list(tools)

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "tags": self.tags,
            "cache_ttl": self.cache_ttl,
        }


class MCPToolProvider(ToolProvider):
    """Tool provider that connects to one or more MCP servers."""

    kind = "mcp"

    def __init__(
        self,
        name: str,
        servers: Mapping[str, Any] | Callable[[], Mapping[str, Any] | None],
        *,
        description: str | None = None,
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
        client_kwargs: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = False,
    ) -> None:
        super().__init__(name, description=description, tags=tags, cache_ttl=cache_ttl)
        if callable(servers):
            self._server_factory = servers
        else:
            self._server_factory = lambda: servers
        self._client_kwargs = client_kwargs or {}
        self._raise_on_error = raise_on_error

    def _build_client(self, config: Mapping[str, Any]) -> MultiServerMCPClient:
        return MultiServerMCPClient(config, **self._client_kwargs)

    async def _load(self) -> Sequence[Any]:
        config = self._server_factory()
        if not config:
            logger.info("MCP provider %s disabled (missing config).", self.name)
            return []

        client = self._build_client(config)
        try:
            return await client.get_tools()
        except Exception as exc:  # pragma: no cover - network/IO heavy
            logger.exception("Failed to load MCP tools for %s", self.name)
            if self._raise_on_error:
                raise ToolManagerError(f"Failed to load tools for {self.name}") from exc
            return []


class CallableToolProvider(ToolProvider):
    """Wraps an arbitrary callable (sync or async) that returns tools."""

    kind = "python"

    def __init__(
        self,
        name: str,
        builder: Callable[[], Sequence[Any]] | Callable[[], Awaitable[Sequence[Any]]],
        *,
        description: str | None = None,
        tags: Sequence[str] | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        super().__init__(name, description=description, tags=tags, cache_ttl=cache_ttl)
        self._builder = builder

    async def _load(self) -> Sequence[Any]:
        result = self._builder()
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        return list(result or [])


@dataclass
class _CacheEntry:
    tools: List[Any]
    expires_at: float | None

    def valid(self) -> bool:
        return self.expires_at is None or self.expires_at > time.time()


class ToolManager:
    """Thread-safe + async-friendly registry for loading/caching tools."""

    def __init__(self) -> None:
        self._providers: Dict[str, ToolProvider] = {}
        self._cache: Dict[str, _CacheEntry] = {}
        self._locks: WeakKeyDictionary[asyncio.AbstractEventLoop, Dict[str, asyncio.Lock]] = (
            WeakKeyDictionary()
        )

    def register_provider(self, provider: ToolProvider, *, override: bool = False) -> None:
        if provider.name in self._providers and not override:
            raise ToolManagerError(f"Tool provider '{provider.name}' already registered")
        self._providers[provider.name] = provider
        self._cache.pop(provider.name, None)

    def is_registered(self, name: str) -> bool:
        return name in self._providers

    def describe(self, name: str) -> Dict[str, Any]:
        provider = self._providers.get(name)
        if not provider:
            raise ToolManagerError(f"Unknown tool provider '{name}'")
        data = provider.metadata()
        entry = self._cache.get(name)
        data["cached"] = bool(entry and entry.valid())
        return data

    def list_providers(self) -> List[Dict[str, Any]]:
        return [self.describe(name) for name in sorted(self._providers.keys())]

    async def get_tools_async(self, name: str, *, refresh: bool = False) -> List[Any]:
        provider = self._providers.get(name)
        if not provider:
            raise ToolManagerError(f"Unknown tool provider '{name}'")

        entry = self._cache.get(name)
        if not refresh and entry and entry.valid():
            return entry.tools

        lock = self._lock_for(name)
        async with lock:
            entry = self._cache.get(name)
            if not refresh and entry and entry.valid():
                return entry.tools

            tools = await provider.load()
            ttl = provider.cache_ttl
            expires_at = (time.time() + ttl) if ttl else None
            self._cache[name] = _CacheEntry(list(tools), expires_at)
            return tools

    def get_tools(self, name: str, *, refresh: bool = False) -> List[Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.get_tools_async(name, refresh=refresh))
        raise ToolManagerError(
            "Cannot call synchronous get_tools inside a running event loop. Use 'await get_tools_async'."
        )

    def clear_cache(self, name: str | None = None) -> None:
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()

    def _lock_for(self, name: str) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        loop_locks = self._locks.get(loop)
        if loop_locks is None:
            loop_locks = {}
            self._locks[loop] = loop_locks
        lock = loop_locks.get(name)
        if lock is None:
            lock = asyncio.Lock()
            loop_locks[name] = lock
        return lock


# Shared singleton used throughout the codebase.
tool_manager = ToolManager()

__all__ = [
    "CallableToolProvider",
    "MCPToolProvider",
    "ToolManager",
    "ToolManagerError",
    "ToolProvider",
    "tool_manager",
]
