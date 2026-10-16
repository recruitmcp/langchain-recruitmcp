"""Live smoke test: tools/list plus one free resolve_location. 0 credits."""
import asyncio
from langchain_recruitmcp import RecruitMCPToolkit

async def main():
    all_tools = await RecruitMCPToolkit(sourcing_only=False).aget_tools()
    src = await RecruitMCPToolkit().aget_tools()
    print("all:", sorted(t.name for t in all_tools))
    print("sourcing_only:", sorted(t.name for t in src))
    t = {x.name: x for x in src}["resolve_location"]
    print("resolve_location:", str(await t.ainvoke({"text": "Ghent, Belgium"}))[:500])

asyncio.run(main())
