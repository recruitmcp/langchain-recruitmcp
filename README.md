# langchain-recruitmcp

LangChain integration for [RecruitMCP](https://recruitmcp.com). It loads RecruitMCP's MCP tools (search people and companies, enrich profiles, find email and phone) as LangChain tools for your agents.

## Install

```bash
pip install langchain-recruitmcp
```

## Set your key

Get a free API key at [recruitmcp.com](https://recruitmcp.com), then:

```bash
export RECRUITMCP_KEY=rmcp_live_...
```

## Use

```python
import asyncio
from langchain_recruitmcp import RecruitMCPToolkit

async def main():
    tools = await RecruitMCPToolkit().aget_tools()
    by_name = {t.name: t for t in tools}
    print(await by_name["resolve_location"].ainvoke({"text": "Ghent, Belgium"}))

asyncio.run(main())
```

With a LangGraph agent. `create_agent` lives in `langchain.agents` from langchain 1.0, and langchain is not a dependency of this package, so install it too (`pip install "langchain-recruitmcp[agents]" langchain-openai`, or `pip install "langchain>=1.0" langchain-openai langchain-recruitmcp`):

```python
import asyncio
from langchain.agents import create_agent
from langchain_recruitmcp import RecruitMCPToolkit

async def main():
    tools = await RecruitMCPToolkit().aget_tools()
    agent = create_agent("openai:gpt-4.1-mini", tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "Find backend engineers in Ghent, Belgium. Dry run only."}]})
    print(result["messages"][-1].content)

asyncio.run(main())
```

This needs `OPENAI_API_KEY`. Any LangChain chat model works.

## Options

| Argument | Default | What it does |
| --- | --- | --- |
| `api_key` | `RECRUITMCP_KEY` env var | Your RecruitMCP key |
| `url` | `RECRUITMCP_MCP_URL` or `https://mcp.recruitmcp.com/mcp` | MCP endpoint |
| `sourcing_only` | `True` | Drops outreach tools only. Uses the tool's `recruitmcp/category` metadata when present, otherwise its name |
| `include_billing` | `False` | Billing tools (`set_auto_refill`, `get_auto_refill`) are dropped unless this is True. Auto-refill charges the saved card |
| `include` | `None` | Keep only these tool names |
| `exclude` | `None` | Drop these tool names |

The tools you get also depend on your key's scopes: the server only lists tools the key may use.

## Credits

`resolve_location` and `search_people` with `dry_run: true` are free. Paid calls show their cost in the response. See [recruitmcp.com/docs/mcp](https://recruitmcp.com/docs/mcp).

## Development

```bash
pip install -e . pytest pytest-asyncio
pytest                                   # unit tests, no network
RECRUITMCP_KEY=... pytest tests/integration_tests   # live, 0 credits
```

## License

MIT
