"""LangChain integration for RecruitMCP."""

from langchain_recruitmcp.toolkits import (
    BILLING_TOOLS,
    DEFAULT_MCP_URL,
    OUTREACH_TOOL_MARKERS,
    RecruitMCPToolkit,
    is_outreach_tool,
)

__all__ = [
    "BILLING_TOOLS",
    "DEFAULT_MCP_URL",
    "OUTREACH_TOOL_MARKERS",
    "RecruitMCPToolkit",
    "is_outreach_tool",
]
__version__ = "0.1.2"
