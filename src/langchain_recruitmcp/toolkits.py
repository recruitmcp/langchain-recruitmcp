"""RecruitMCP toolkit: RecruitMCP's MCP tools as LangChain tools."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Iterable, Optional

from langchain_core.tools import BaseTool

DEFAULT_MCP_URL = "https://mcp.recruitmcp.com/mcp"
KEY_ENV_VAR = "RECRUITMCP_KEY"
URL_ENV_VAR = "RECRUITMCP_MCP_URL"

# Backstop only: the server sets _meta['recruitmcp/category'] on every tool, and
# hides outreach tools from tools/list while outreach is off. These name
# fragments are used only when a tool has no category. Name fragments that mark a tool as outreach (drafting, sequencing, sending,
# approving, connecting accounts). Matching is case-insensitive.
OUTREACH_TOOL_MARKERS: tuple[str, ...] = (
    "outreach",
    "send",
    "approve",
    "sequence",
    "draft",
    "connect_outreach_account",
    "enrollment",
    "conversation",
    "replies",
)


CATEGORY_META_KEY = "recruitmcp/category"


def tool_category(tool: Any) -> Optional[str]:
    """Return the server-declared category from the tool's MCP ``_meta``, if any."""
    metadata = getattr(tool, "metadata", None) or {}
    meta = metadata.get("_meta") or {}
    category = meta.get(CATEGORY_META_KEY) if isinstance(meta, dict) else None
    return category if isinstance(category, str) else None


def is_outreach_tool(tool: Any) -> bool:
    """Return True for an outreach tool.

    The primary signal is ``_meta['recruitmcp/category']``, which the server
    sets on its tools. Only when it is missing does this fall back to matching
    the tool name against ``OUTREACH_TOOL_MARKERS``.
    Accepts a tool or a tool name.
    """
    if not isinstance(tool, str):
        category = tool_category(tool)
        if category is not None:
            return category == "outreach"
        tool = tool.name
    lowered = tool.lower()
    return any(marker in lowered for marker in OUTREACH_TOOL_MARKERS)


class RecruitMCPToolkit:
    """Load RecruitMCP's MCP tools for a LangChain or LangGraph agent.

    The key is read from ``RECRUITMCP_KEY`` unless ``api_key`` is passed.
    Which tools come back also depends on the key's scopes: the server only
    lists tools the key may use.

    Args:
        api_key: RecruitMCP API key. Defaults to the ``RECRUITMCP_KEY`` env var.
        url: MCP endpoint. Defaults to ``RECRUITMCP_MCP_URL`` or the public endpoint.
        sourcing_only: When True (the default), outreach tools are dropped.
        include: Optional allowlist of tool names, applied after ``sourcing_only``.
        exclude: Optional tool names to drop.

    Example:
        .. code-block:: python

            toolkit = RecruitMCPToolkit()
            tools = await toolkit.aget_tools()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        url: Optional[str] = None,
        sourcing_only: bool = True,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
    ) -> None:
        key = api_key or os.environ.get(KEY_ENV_VAR)
        if not key:
            raise ValueError(
                f"No RecruitMCP API key. Set the {KEY_ENV_VAR} environment variable "
                "or pass api_key."
            )
        self._api_key = key
        self.url = url or os.environ.get(URL_ENV_VAR) or DEFAULT_MCP_URL
        self.sourcing_only = sourcing_only
        self.include = set(include) if include is not None else None
        self.exclude = set(exclude or ())
        self._tools: Optional[list[BaseTool]] = None

    def __repr__(self) -> str:  # never show the key
        return (
            f"RecruitMCPToolkit(url={self.url!r}, sourcing_only={self.sourcing_only!r})"
        )

    def connection(self) -> dict[str, Any]:
        """Connection config for ``MultiServerMCPClient``."""
        return {
            "transport": "streamable_http",
            "url": self.url,
            "headers": {"Authorization": f"Bearer {self._api_key}"},
        }

    def _client(self) -> Any:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        return MultiServerMCPClient({"recruitmcp": self.connection()})

    def _filter(self, tools: Iterable[BaseTool]) -> list[BaseTool]:
        kept = []
        for tool in tools:
            if self.sourcing_only and is_outreach_tool(tool):
                continue
            if self.include is not None and tool.name not in self.include:
                continue
            if tool.name in self.exclude:
                continue
            kept.append(tool)
        return kept

    async def aget_tools(self) -> list[BaseTool]:
        """Fetch the tool list from the server and return the filtered tools."""
        if self._tools is None:
            self._tools = await self._client().get_tools()
        return self._filter(self._tools)

    def get_tools(self) -> list[BaseTool]:
        """Sync wrapper around :meth:`aget_tools`. Not for use inside a running loop."""
        return asyncio.run(self.aget_tools())
