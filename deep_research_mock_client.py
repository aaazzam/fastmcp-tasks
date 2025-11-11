"""
Deep Research Client - Demonstrates SEP-1686 Background Tasks

This client demonstrates the key benefits of background tasks for long-running operations:

1. Fire-and-forget: Submit research, do other work
2. Status monitoring: Poll progress while research runs
3. Connection independence: Could disconnect and reconnect
4. Multi-client capable: Share task_id with teammates

Based on the real-world use case from SEP-1686:
"Deep research tools spawn multiple research agents... takes 10-30 minutes.
Model cannot resume until receiving a new user message."
"""

import asyncio
from datetime import datetime

from fastmcp import Client

# Import the server for in-memory demo
from deep_research_mock_server import mcp


async def demonstrate_fire_and_forget():
    """
    Pattern 1: Fire-and-forget

    Submit long-running research and do other work while it executes.
    This is IMPOSSIBLE with regular tool calls or asyncio.gather.
    """
    print("=" * 70)
    print("Demo 1: Fire-and-Forget Pattern")
    print("=" * 70)

    client = Client(mcp)

    async with client:
        # Submit research task
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Submitting deep research task...")
        task = await client.call_tool(
            "deep_research",
            {"query": "Find hedge funds that write Python in London"},
            task=True,
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Task submitted! Task ID: {task}")
        print("\nThis is the power of background tasks:")
        print("- Research is running on the server")
        print("- Client is free to do other work")
        print("- Could even disconnect and reconnect")
        print("- Share this task_id with teammates to check progress\n")

        # Simulate doing other work
        print("Doing other work while research runs...")
        for i in range(3):
            await asyncio.sleep(2)
            print(f"  - Other work step {i + 1}/3 completed")

        print("\nLet's check on our research...")

        # Check status
        status = await task.status()
        print(f"Research status: {status.status}")

        # Wait for completion
        print("\nWaiting for research to complete...")
        result = await task.result()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Research completed!")
        print(f"Total time: {result.data['timing']['total_seconds']}s")
        print("\nReport preview (first 500 chars):")
        print(result.data['report'][:500] + "...")


async def demonstrate_status_monitoring(client):
    """
    Pattern 2: Active status monitoring

    Poll task status during execution to show progress to user.
    Essential for long-running operations (minutes/hours).
    """
    print("\n" + "=" * 70)
    print("Demo 2: Status Monitoring Pattern")
    print("=" * 70)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting monitored research...")
    task = await client.call_tool(
        "deep_research",
        {"query": "Latest developments in AI agent frameworks"},
        task=True,
    )

    print("\nMonitoring research progress (polling every 2 seconds):\n")

    # Poll for completion
    check_count = 0
    while True:
        check_count += 1
        status = await task.status()

        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] Check #{check_count}: Status = {status.status}")

        if status.status in ["completed", "failed", "cancelled"]:
            break

        # Wait before next check
        await asyncio.sleep(2)

    # Get result
    result = await task.result()

    print(f"\n✓ Research completed after {check_count} status checks")

    # Defensive check
    if result.data is None:
        print("⚠️  Warning: Result data is None")
        print(f"   Result object: {result}")
        return

    print(f"✓ Total execution time: {result.data['timing']['total_seconds']}s")
    print(f"✓ Found {len(result.data['search_results'])} search results")


async def demonstrate_multi_retrieval():
    """
    Pattern 3: Multiple result retrieval

    Get the same result multiple times - impossible with normal tool calls.
    Useful for sharing results across devices or team members.
    """
    print("\n" + "=" * 70)
    print("Demo 3: Multiple Result Retrieval Pattern")
    print("=" * 70)

    client = Client(mcp)

    async with client:
        print("\nSubmitting research task...")
        task = await client.call_tool(
            "deep_research",
            {"query": "Machine learning ops best practices"},
            task=True,
        )

        # Wait for completion
        print("Waiting for research...")
        result1 = await task.result()
        print(f"✓ First retrieval completed at {datetime.now().strftime('%H:%M:%S')}")

        # Simulate accessing from different device/session
        print("\nSimulating access from another device/session...")
        await asyncio.sleep(2)

        # Get result again
        result2 = await task.result()
        print(f"✓ Second retrieval completed at {datetime.now().strftime('%H:%M:%S')}")

        print("\n💡 Key insight:")
        print("   Both retrievals got the same result!")
        print("   Results are cached on server until keepAlive expires")
        print("   Perfect for:")
        print("   - Accessing from mobile after starting on laptop")
        print("   - Sharing results with team members")
        print("   - Recovering from client crashes")


async def demonstrate_concurrent_research():
    """
    Pattern 4: Multiple concurrent research tasks

    Submit multiple long-running research tasks that execute in parallel.
    Shows how background tasks enable true concurrent workflows.
    """
    print("\n" + "=" * 70)
    print("Demo 4: Concurrent Research Tasks")
    print("=" * 70)

    client = Client(mcp)

    async with client:
        print("\nLaunching 3 research tasks in parallel...")

        # Submit all research tasks
        task_a = await client.call_tool(
            "deep_research",
            {"query": "Quantum computing applications"},
            task=True,
        )
        task_b = await client.call_tool(
            "deep_research",
            {"query": "Sustainable energy technologies"},
            task=True,
        )
        task_c = await client.call_tool(
            "deep_research",
            {"query": "Biotechnology innovations"},
            task=True,
        )

        print("✓ All 3 tasks submitted and running in parallel\n")

        # Monitor all tasks
        print("Monitoring all tasks:")
        tasks = {"Quantum": task_a, "Energy": task_b, "Biotech": task_c}
        completed = set()

        while len(completed) < len(tasks):
            states = []
            for name, task in tasks.items():
                if name not in completed:
                    status = await task.status()
                    if status.status == "completed":
                        completed.add(name)
                        states.append(f"{name}: ✓ DONE")
                    else:
                        states.append(f"{name}: {status.status}")
                else:
                    states.append(f"{name}: ✓ DONE")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] {' | '.join(states)}")

            if len(completed) < len(tasks):
                await asyncio.sleep(3)

        # Get all results
        results = await asyncio.gather(task_a, task_b, task_c)

        print(f"\n✓ All research completed!")
        for name, result in zip(["Quantum", "Energy", "Biotech"], results):
            print(f"  {name}: {result.data['timing']['total_seconds']}s")


async def main():
    """Run all demonstration patterns"""
    print("\n" + "=" * 70)
    print("FastMCP Background Tasks: Deep Research Demo")
    print("=" * 70)
    print("\nThis demo shows why background tasks matter for long-running operations.")
    print("Based on SEP-1686 use case: 'Deep research tools that take 10-30 minutes'\n")

    # Run all demonstrations
    await demonstrate_fire_and_forget()
    await demonstrate_status_monitoring()
    await demonstrate_multi_retrieval()
    await demonstrate_concurrent_research()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Fire-and-forget: Submit work, do other things")
    print("2. Status monitoring: Track progress on long operations")
    print("3. Multiple retrieval: Access results from anywhere")
    print("4. Concurrent tasks: Run multiple research projects in parallel")
    print("\n💡 These patterns are IMPOSSIBLE with regular tool calls or asyncio.gather!")
    print("   Background tasks enable real-world workflows for operations taking")
    print("   minutes or hours.\n")


if __name__ == "__main__":
    asyncio.run(main())
