"""Live check: lists tools and calls the free resolve_location. Spends 0 credits."""
import os

import pytest

from langchain_recruitmcp import RecruitMCPToolkit

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("RECRUITMCP_KEY"), reason="RECRUITMCP_KEY not set"),
]


async def test_list_and_resolve_location():
    tools = {t.name: t for t in await RecruitMCPToolkit().aget_tools()}
    assert "resolve_location" in tools
    result = await tools["resolve_location"].ainvoke({"text": "Ghent, Belgium"})
    assert result
