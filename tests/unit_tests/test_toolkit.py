from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import StructuredTool

from langchain_recruitmcp import DEFAULT_MCP_URL, RecruitMCPToolkit, is_outreach_tool

NAMES = [
    "resolve_location",
    "search_people",
    "enrich_profiles",
    "get_people_job",
    "set_candidate_status",
    "save_to_list",
    "get_auto_refill",
    "list_billing_transactions",
    "create_outreach_draft",
    "send_message",
    "approve_sequence_step",
]


def _tool(name: str, category=None) -> StructuredTool:
    t = StructuredTool.from_function(func=lambda: "ok", name=name, description=name)
    if category is not None:
        t.metadata = {"_meta": {"recruitmcp/category": category}}
    return t


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_tools = AsyncMock(return_value=[_tool(n) for n in NAMES])
    with patch(
        "langchain_mcp_adapters.client.MultiServerMCPClient", return_value=client
    ) as cls:
        yield cls, client


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("RECRUITMCP_KEY", raising=False)
    with pytest.raises(ValueError, match="RECRUITMCP_KEY"):
        RecruitMCPToolkit()


def test_key_from_env_and_connection(monkeypatch):
    monkeypatch.setenv("RECRUITMCP_KEY", "test-key")
    monkeypatch.delenv("RECRUITMCP_MCP_URL", raising=False)
    conn = RecruitMCPToolkit().connection()
    assert conn["url"] == DEFAULT_MCP_URL
    assert conn["transport"] == "streamable_http"
    assert conn["headers"]["Authorization"] == "Bearer test-key"


def test_repr_hides_key():
    assert "secret-123" not in repr(RecruitMCPToolkit(api_key="secret-123"))


def test_url_override(monkeypatch):
    monkeypatch.setenv("RECRUITMCP_MCP_URL", "https://example.test/mcp")
    assert RecruitMCPToolkit(api_key="k").url == "https://example.test/mcp"
    assert RecruitMCPToolkit(api_key="k", url="https://x.test/mcp").url == "https://x.test/mcp"


@pytest.mark.parametrize(
    "name,expected",
    [("send_message", True), ("approve_step", True), ("create_outreach_draft", True),
     ("list_enrollments", True), ("update_enrollment", True), ("get_conversation", True), ("list_replies", True), ("connect_outreach_account", True), ("search_people", False), ("save_to_list", False), ("resolve_location", False)],
)
def test_is_outreach_tool(name, expected):
    assert is_outreach_tool(name) is expected


async def test_sourcing_only_default(mock_client):
    cls, _ = mock_client
    tools = await RecruitMCPToolkit(api_key="k").aget_tools()
    assert [t.name for t in tools] == NAMES[:8]
    config = cls.call_args.args[0]["recruitmcp"]
    assert config["headers"]["Authorization"] == "Bearer k"


async def test_all_tools(mock_client):
    tools = await RecruitMCPToolkit(api_key="k", sourcing_only=False).aget_tools()
    assert [t.name for t in tools] == NAMES


async def test_include_exclude(mock_client):
    tk = RecruitMCPToolkit(api_key="k", include={"search_people", "send_message"})
    assert [t.name for t in await tk.aget_tools()] == ["search_people"]
    tk = RecruitMCPToolkit(api_key="k", exclude={"enrich_profiles"})
    assert "enrich_profiles" not in [t.name for t in await tk.aget_tools()]


async def test_tools_cached(mock_client):
    _, client = mock_client
    tk = RecruitMCPToolkit(api_key="k")
    await tk.aget_tools()
    await tk.aget_tools()
    assert client.get_tools.await_count == 1


def test_sync_get_tools(mock_client):
    assert len(RecruitMCPToolkit(api_key="k").get_tools()) == 8


def test_meta_category_wins_over_name():
    # name looks like outreach, but the server says sourcing
    assert is_outreach_tool(_tool("send_digest", "sourcing")) is False
    # name looks harmless, but the server says outreach
    assert is_outreach_tool(_tool("plan_campaign", "outreach")) is True


def test_name_fallback_without_meta():
    assert is_outreach_tool(_tool("send_message")) is True
    assert is_outreach_tool(_tool("search_people")) is False
    t = _tool("list_replies")
    t.metadata = {"_meta": {"other": "x"}}
    assert is_outreach_tool(t) is True


async def test_filter_uses_meta(monkeypatch):
    tools = [_tool("plan_campaign", "outreach"), _tool("send_digest", "sourcing"),
             _tool("search_people", "sourcing"), _tool("save_sequence")]
    client = MagicMock()
    client.get_tools = AsyncMock(return_value=tools)
    with patch("langchain_mcp_adapters.client.MultiServerMCPClient", return_value=client):
        names = [t.name for t in await RecruitMCPToolkit(api_key="k").aget_tools()]
    assert names == ["send_digest", "search_people"]
