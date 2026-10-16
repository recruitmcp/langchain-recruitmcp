# Changelog

## 0.1.0 (unreleased)

- First release of `RecruitMCPToolkit`: loads RecruitMCP's MCP tools through `langchain-mcp-adapters`.
- Key from `RECRUITMCP_KEY`, endpoint override with `RECRUITMCP_MCP_URL`.
- `sourcing_only=True` by default drops outreach tools. `include` and `exclude` filter by name.
- Outreach filter uses the server's `_meta['recruitmcp/category']`. Tool names are a backstop when the category is missing.
