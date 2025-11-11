"""
Deep Research Orchestrated Client - Task Composition Pattern

This demonstrates the power of MCP background tasks for multi-agent workflows.
Instead of a single monolithic tool, we compose smaller tools into a pipeline:

1. plan_research - Get search plan from Claude
2. web_search (multiple) - Spawn N parallel search tasks (like TaskGroup!)
3. analyze_research - Synthesize results with Claude

This mirrors the pydantic_ai pattern:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(search_agent.run(step)) for step in steps]

But uses MCP background tasks instead!
"""

import asyncio
from datetime import datetime

from fastmcp import Client

# Import the server
from deep_research_server import mcp


async def orchestrated_deep_research(query: str):
    """
    Orchestrate deep research using composable MCP tasks.

    This demonstrates task composition - the pattern from pydantic_ai
    but using MCP background tasks instead of asyncio.TaskGroup!
    """
    print(f"\nQuery: {query}\n")

    client = Client(mcp)

    async with client:
        # Step 1: Create research plan
        print("Creating research plan...")
        plan_result = await client.call_tool("plan_research", {"query": query})
        plan = plan_result.data
        print(f"✓ Plan created with {len(plan['search_steps'])} search steps\n")

        # Step 2: Launch parallel search tasks (like pydantic_ai TaskGroup)
        print(f"Launching {len(plan['search_steps'])} search tasks in parallel...")
        search_tasks = [
            await client.call_tool("web_search", {"search_terms": step}, task=True)
            for step in plan['search_steps']
        ]
        print(f"✓ {len(search_tasks)} tasks running\n")

        # Gather results
        print("Waiting for searches to complete...")
        search_results = await asyncio.gather(*search_tasks)
        search_outputs = [result.data for result in search_results]
        print(f"✓ Collected {len(search_outputs)} results\n")

        # Step 3: Analyze results
        print("Analyzing results...")
        analysis_task = await client.call_tool(
            "analyze_research",
            {
                "query": query,
                "search_results": search_outputs,
                "instructions": plan['analysis_instructions'],
            },
            task=True,
        )
        analysis_result = await analysis_task
        report = analysis_result.data

        print("\n" + "=" * 80)
        print("RESEARCH REPORT")
        print("=" * 80)
        print(report)
        print("=" * 80)


async def main():
    query = "What are the latest developments in MCP (Model Context Protocol)?"

    print("=" * 80)
    print("Deep Research: Task Composition Demo")
    print("=" * 80)

    await orchestrated_deep_research(query)


if __name__ == "__main__":
    asyncio.run(main())
