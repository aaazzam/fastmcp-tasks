"""
Deep Research Client - REAL VERSION with AI Agents

This client uses the real deep_research_server.py with pydantic_ai agents:
- Claude Sonnet 4.5 for planning and analysis
- Gemini 2.5 Flash for web searches

Requires .env file with API keys.
"""

import asyncio
from datetime import datetime

from fastmcp import Client

# Import the REAL server with AI agents
from deep_research_server import mcp


async def demonstrate_real_research():
    """
    Run actual deep research with real AI agents.

    This will take 10-30 minutes depending on:
    - Query complexity
    - Number of searches needed
    - API response times
    """
    print("=" * 70)
    print("Real Deep Research with AI Agents")
    print("=" * 70)

    client = Client(mcp)

    async with client:
        query = "What are the latest developments in MCP (Model Context Protocol) and how are developers using it?"

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting REAL deep research...")
        print(f"Query: {query}")
        print("\nThis will use:")
        print("  - Claude Sonnet 4.5 for planning and analysis")
        print("  - Gemini 2.5 Flash for web searches")
        print("  - Real web search results")
        print("\nExpected time: 10-30 minutes")
        print("\nYou can close this client and reconnect later - the task will continue!")

        # Submit the research task
        task = await client.call_tool(
            "deep_research",
            {"query": query},
            task=True,
        )

        print(f"\n✓ Task submitted at {datetime.now().strftime('%H:%M:%S')}")
        print("  Task is running on server with real AI agents")
        print("  Monitoring progress...\n")

        # Monitor progress
        check_count = 0
        start_time = datetime.now()

        while True:
            check_count += 1
            status = await task.status()

            elapsed = (datetime.now() - start_time).total_seconds()
            timestamp = datetime.now().strftime('%H:%M:%S')

            print(f"[{timestamp}] Check #{check_count} (elapsed: {elapsed:.0f}s): Status = {status.status}")

            if status.status in ["completed", "failed", "cancelled"]:
                break

            # Check every 5 seconds for real tasks (they take longer)
            await asyncio.sleep(5)

        # Get result
        print("\n" + "=" * 70)
        print("Research Complete!")
        print("=" * 70)

        result = await task.result()

        if result.data is None:
            print("⚠️  Warning: Result data is None")
            return

        print(f"\n✓ Total checks: {check_count}")
        print(f"✓ Total time: {(datetime.now() - start_time).total_seconds():.1f}s")
        print(f"✓ Agents used: {', '.join(result.data['metadata']['agents_used'])}")

        print("\n" + "=" * 70)
        print("RESEARCH REPORT")
        print("=" * 70)
        print(result.data['report'])

        print("\n" + "=" * 70)
        print("💡 Key Insight: This task ran on the server with real AI!")
        print("   - You could have closed this client and reconnected")
        print("   - Another team member could check status with the task_id")
        print("   - Results persist and can be retrieved multiple times")
        print("=" * 70)


async def main():
    """Run real deep research demo"""
    print("\n" + "=" * 70)
    print("FastMCP Background Tasks: REAL Deep Research")
    print("=" * 70)
    print("\nThis demo uses actual AI agents and will take 10-30 minutes.")
    print("Perfect example of why background tasks matter for long operations.\n")

    await demonstrate_real_research()

    print("\n✓ Demo complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
