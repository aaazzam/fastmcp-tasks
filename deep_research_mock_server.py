"""
Deep Research Mock Server - Demonstrates SEP-1686 Background Tasks

This simulates a deep research system like the pydantic_ai example, but uses
mock delays instead of real AI agents. Perfect for demos without API keys.

Simulates the research flow:
1. Plan generation (5s) - Analyze query and design research plan
2. Parallel web searches (8s each, run concurrently) - Gather information
3. Analysis (10s) - Synthesize findings into final report

Total time: ~23 seconds (5s + 8s + 10s), demonstrating fire-and-forget patterns.
"""

import asyncio
import time
from datetime import datetime

from fastmcp import FastMCP, settings

# Enable experimental task support
settings.experimental.enable_docket = True
settings.experimental.enable_tasks = True

# Create the FastMCP server
mcp = FastMCP(
    name="deep-research-mock-server",
    instructions="A mock deep research server demonstrating long-running background tasks",
)


async def simulate_planning(query: str) -> dict:
    """Simulate AI planning phase - analyzing query and creating research plan."""
    print(f"  [PLANNING] Analyzing query: '{query}'")
    await asyncio.sleep(5)  # Simulate planning time

    # Generate mock search steps
    search_steps = [
        "recent developments in query topic",
        "best practices and industry standards",
        "expert opinions and analysis",
    ]

    return {
        "executive_summary": f"Research plan for: {query}",
        "search_steps": search_steps,
        "analysis_instructions": "Synthesize findings into comprehensive report",
    }


async def simulate_web_search(search_term: str, step_num: int) -> dict:
    """Simulate web search for given terms."""
    print(f"  [SEARCH {step_num}] Searching: '{search_term}'")
    await asyncio.sleep(8)  # Simulate search time

    return {
        "search_term": search_term,
        "results": f"Mock results for '{search_term}': Found 42 relevant articles...",
        "summary": f"Summary of findings about {search_term}",
    }


async def simulate_analysis(query: str, search_results: list[dict]) -> str:
    """Simulate AI analysis of gathered information."""
    print(f"  [ANALYSIS] Synthesizing {len(search_results)} search results")
    await asyncio.sleep(10)  # Simulate analysis time

    # Create mock report
    report = f"""
# Deep Research Report: {query}

## Executive Summary
Based on comprehensive research across multiple sources, this report synthesizes
findings from {len(search_results)} distinct search queries.

## Key Findings
"""

    for i, result in enumerate(search_results, 1):
        report += f"\n### Finding {i}: {result['search_term']}\n"
        report += f"{result['summary']}\n"

    report += """
## Conclusion
The research indicates significant developments in this area. Further investigation
may be warranted in specific sub-domains identified during the analysis phase.

## Methodology
This research employed a multi-step approach:
1. Query analysis and research planning
2. Parallel information gathering across multiple sources
3. Synthesis and analysis of findings
"""

    return report


@mcp.tool(task=True)
async def deep_research(query: str) -> dict:
    """
    Perform deep research on a query using multi-step AI analysis.

    This is a long-running operation (20-30 seconds) that:
    1. Analyzes the query and creates a research plan
    2. Runs multiple web searches in parallel
    3. Synthesizes findings into a comprehensive report

    Perfect demonstration of SEP-1686 background tasks:
    - Takes significant time (20+ seconds)
    - Client can disconnect and reconnect
    - Multiple clients can monitor progress via task_id
    - Shows real-world use case (deep research from SEP-1686)

    Args:
        query: The research question or topic to investigate

    Returns:
        dict with keys:
            - query: Original query
            - plan: Research plan details
            - search_results: Results from web searches
            - report: Final research report
            - timing: Execution timing information
    """
    start_time = time.time()
    print(f"\n[SERVER] Starting deep research for: '{query}'")
    print(f"[SERVER] This will take ~23 seconds")

    # Step 1: Planning (5s)
    plan_start = time.time()
    plan = await simulate_planning(query)
    plan_time = time.time() - plan_start
    print(f"  [PLANNING] Completed in {plan_time:.1f}s")

    # Step 2: Parallel searches (8s each, run concurrently)
    search_start = time.time()
    async with asyncio.TaskGroup() as tg:
        search_tasks = [
            tg.create_task(simulate_web_search(step, i + 1))
            for i, step in enumerate(plan["search_steps"])
        ]

    search_results = [task.result() for task in search_tasks]
    search_time = time.time() - search_start
    print(f"  [SEARCH] Completed {len(search_results)} searches in {search_time:.1f}s")

    # Step 3: Analysis (10s)
    analysis_start = time.time()
    report = await simulate_analysis(query, search_results)
    analysis_time = time.time() - analysis_start
    print(f"  [ANALYSIS] Completed in {analysis_time:.1f}s")

    total_time = time.time() - start_time
    print(f"[SERVER] Deep research completed in {total_time:.1f}s")

    return {
        "query": query,
        "plan": plan,
        "search_results": search_results,
        "report": report,
        "timing": {
            "total_seconds": round(total_time, 2),
            "planning_seconds": round(plan_time, 2),
            "search_seconds": round(search_time, 2),
            "analysis_seconds": round(analysis_time, 2),
        },
        "completed_at": datetime.now().isoformat(),
    }


@mcp.tool()
def quick_lookup(topic: str) -> str:
    """Quick lookup for comparison - executes immediately without background task."""
    return f"Quick lookup result for '{topic}': Basic information retrieved in <1s"


if __name__ == "__main__":
    mcp.run(transport="stdio")
