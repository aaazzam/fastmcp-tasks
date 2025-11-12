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
import logging
from datetime import datetime

from fastmcp import Client

# Import the server
from deep_research_server import mcp
from task_logger import enable_task_polling_logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("deep-research-client")


async def orchestrated_deep_research(query: str):
    """
    Orchestrate deep research using composable MCP tasks.

    This demonstrates task composition - the pattern from pydantic_ai
    but using MCP background tasks instead of asyncio.TaskGroup!
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting deep research for: '{query}'")
    logger.info("=" * 80)

    print(f"\nQuery: {query}\n")

    client = Client(mcp)
    enable_task_polling_logs(client)

    async with client:
        # Step 1: Create research plan
        logger.info("STEP 1: Creating research plan...")
        print("Creating research plan...")

        step_start = datetime.now()
        plan_result = await client.call_tool("plan_research", {"query": query})
        plan = plan_result.data
        step_duration = (datetime.now() - step_start).total_seconds()

        logger.info(f"✓ Plan created in {step_duration:.1f}s")
        logger.info(f"  - {len(plan['search_steps'])} search steps planned")
        logger.info(f"  - Executive summary: {plan['executive_summary'][:80]}...")
        print(f"✓ Plan created with {len(plan['search_steps'])} search steps\n")

        # Step 2: Launch parallel search tasks (like pydantic_ai TaskGroup)
        logger.info(f"STEP 2: Launching {len(plan['search_steps'])} parallel search tasks...")
        print(f"Launching {len(plan['search_steps'])} search tasks in parallel...")

        for i, step in enumerate(plan['search_steps'], 1):
            logger.info(f"  Task {i}: '{step}'")

        step_start = datetime.now()
        search_tasks = [
            await client.call_tool("web_search", {"search_terms": step}, task=True)
            for step in plan['search_steps']
        ]
        logger.info(f"✓ {len(search_tasks)} tasks launched")
        print(f"✓ {len(search_tasks)} tasks running\n")

        # Gather results
        logger.info("Waiting for all search tasks to complete...")
        print("Waiting for searches to complete...")

        search_results = await asyncio.gather(*search_tasks)
        search_outputs = [result.data for result in search_results]
        step_duration = (datetime.now() - step_start).total_seconds()

        logger.info(f"✓ All {len(search_outputs)} searches completed in {step_duration:.1f}s")
        for i, output in enumerate(search_outputs, 1):
            logger.info(f"  Result {i}: {len(output)} chars")
        print(f"✓ Collected {len(search_outputs)} results\n")

        # Step 3: Analyze results
        logger.info("STEP 3: Analyzing combined search results...")
        print("Analyzing results...")

        step_start = datetime.now()
        analysis_task = await client.call_tool(
            "analyze_research",
            {
                "query": query,
                "search_results": search_outputs,
                "instructions": plan['analysis_instructions'],
            },
            task=True,
        )
        logger.info("Analysis task launched, waiting for completion...")

        analysis_result = await analysis_task
        report = analysis_result.data
        step_duration = (datetime.now() - step_start).total_seconds()

        total_duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"✓ Analysis completed in {step_duration:.1f}s")
        logger.info(f"Report length: {len(report)} chars")
        logger.info("=" * 80)
        logger.info(f"TOTAL RESEARCH TIME: {total_duration:.1f}s")
        logger.info("=" * 80)

        print("\n" + "=" * 80)
        print("RESEARCH REPORT")
        print("=" * 80)
        print(report)
        print("=" * 80)


async def main():
    query = "What are the latest developments in MCP (Model Context Protocol)? Specifically SEP-1686"

    logger.info("\n")
    logger.info("*" * 80)
    logger.info("Deep Research: Task Composition Demo")
    logger.info("*" * 80)

    print("=" * 80)
    print("Deep Research: Task Composition Demo")
    print("=" * 80)

    await orchestrated_deep_research(query)

    logger.info("\nDemo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
