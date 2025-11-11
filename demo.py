"""
Standalone demo of FastMCP background tasks (SEP-1686)

This script demonstrates TRUE concurrent task execution using the sep-1686 branch.

IMPORTANT: You must enable experimental settings for concurrent execution:
    settings.experimental.enable_docket = True
    settings.experimental.enable_tasks = True

With these enabled, tasks run concurrently! Example 2 shows 3 tasks completing
in ~3 seconds total (not 6s), proving concurrent execution works.
"""

import asyncio
import time
from datetime import datetime

from fastmcp import Client, FastMCP, settings

# Enable experimental task support
settings.experimental.enable_docket = True
settings.experimental.enable_tasks = True

# Create the server
server = FastMCP(name="demo-server")


@server.tool(task=True)
async def long_running_task(duration: int, task_name: str) -> dict:
    """
    A long-running task that sleeps for the specified duration.

    Args:
        duration: How many seconds to run
        task_name: A name for this task instance

    Returns:
        Results of the task execution
    """
    start = time.time()
    print(f"  [SERVER] Task '{task_name}' starting, will run for {duration}s")

    await asyncio.sleep(duration)  # Non-blocking async sleep

    elapsed = time.time() - start
    print(f"  [SERVER] Task '{task_name}' completed after {elapsed:.2f}s")

    return {
        "task_name": task_name,
        "requested_duration": duration,
        "actual_duration": round(elapsed, 2),
        "completed_at": datetime.now().isoformat(),
        "message": f"Task '{task_name}' finished successfully!",
    }


@server.tool()
def instant_tool(message: str) -> str:
    """A regular tool that executes immediately (not task-enabled)"""
    return f"Instant response: {message}"


async def run_demo():
    """Run the complete demo showing task lifecycle"""
    print("=" * 60)
    print("FastMCP Background Tasks Demo (SEP-1686)")
    print("=" * 60)

    # Create client connected to our server
    client = Client(server)

    async with client:
        print(f"\nConnected to server: {server.name}\n")

        # Example 0: COMPARISON - Three Different Approaches
        print("=" * 70)
        print("COMPARISON: Three Ways to Call Multiple Tools")
        print("=" * 70)

        # Part A: Sequential (await each call one by one)
        print("\nApproach A: Sequential calls (one at a time)")
        print("-" * 70)
        sequential_start = time.time()

        print("[CLIENT] Calling 3 tools sequentially...")
        result1 = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "sequential-A"},
            task=False,
        )
        result2 = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "sequential-B"},
            task=False,
        )
        result3 = await client.call_tool(
            "long_running_task",
            {"duration": 1, "task_name": "sequential-C"},
            task=False,
        )

        sequential_elapsed = time.time() - sequential_start
        print(f"[CLIENT] ⏱️  Sequential took: {sequential_elapsed:.2f}s\n")

        # Part B: asyncio.gather with task=False
        print("Approach B: asyncio.gather with task=False")
        print("-" * 70)
        gather_start = time.time()

        print("[CLIENT] Using asyncio.gather on regular tool calls...")
        results = await asyncio.gather(
            client.call_tool("long_running_task", {"duration": 3, "task_name": "gather-A"}, task=False),
            client.call_tool("long_running_task", {"duration": 2, "task_name": "gather-B"}, task=False),
            client.call_tool("long_running_task", {"duration": 1, "task_name": "gather-C"}, task=False),
        )

        gather_elapsed = time.time() - gather_start
        print(f"[CLIENT] ⏱️  asyncio.gather took: {gather_elapsed:.2f}s\n")

        # Part C: Background tasks (task=True)
        print("Approach C: Background tasks (task=True)")
        print("-" * 70)
        task_start = time.time()

        print("[CLIENT] Launching background tasks...")
        task1 = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "background-A"},
            task=True,
        )
        task2 = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "background-B"},
            task=True,
        )
        task3 = await client.call_tool(
            "long_running_task",
            {"duration": 1, "task_name": "background-C"},
            task=True,
        )

        print("[CLIENT] Tasks launched, waiting for completion...")
        results = await asyncio.gather(task1, task2, task3)

        task_elapsed = time.time() - task_start
        print(f"[CLIENT] ⏱️  Background tasks took: {task_elapsed:.2f}s\n")

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Sequential:        {sequential_elapsed:.2f}s (baseline)")
        print(f"asyncio.gather:    {gather_elapsed:.2f}s ({sequential_elapsed/gather_elapsed:.2f}x faster)")
        print(f"Background tasks:  {task_elapsed:.2f}s ({sequential_elapsed/task_elapsed:.2f}x faster)")
        print()
        print("💡 Key insight: asyncio.gather ALSO gives you concurrency!")
        print("   Both approaches run tasks in parallel with similar performance.")
        print()
        print("   So when should you use task=True? When you need:")
        print("   - Status polling while tasks run")
        print("   - Fire-and-forget (submit now, check later)")
        print("   - Ability to do other work before checking results")
        print()

        # Show what you CAN'T do with asyncio.gather
        print("Example: What tasks=True enables (impossible with asyncio.gather)")
        print("-" * 70)

        # Submit tasks
        long_task = await client.call_tool(
            "long_running_task",
            {"duration": 5, "task_name": "long-running"},
            task=True,
        )
        print("[CLIENT] Submitted long task (5s), doing other work...")

        # Do other work while it runs!
        for i in range(3):
            await asyncio.sleep(1)
            status = await long_task.status()
            print(f"  [{i+1}s] Task status: {status.status} (still working...)")

        # Get result when ready
        print("[CLIENT] Now waiting for final result...")
        result = await long_task.result()
        print(f"[CLIENT] Got result: {result.data['message']}")
        print()
        print("⚠️  You can't poll status like this with asyncio.gather!")
        print()

        # Example 1: Simple task with direct await
        print("Example 1: Call task and await immediately")
        print("-" * 60)
        task1 = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "quick-task"},
            task=True,
        )
        print(f"[CLIENT] Task object created: {type(task1).__name__}")
        result1 = await task1
        print(f"[CLIENT] Result: {result1.data}\n")

        # Example 2: Multiple concurrent tasks
        print("Example 2: Launch multiple tasks concurrently")
        print("-" * 60)
        start_time = time.time()
        print(f"[CLIENT] Starting 3 tasks simultaneously at {datetime.now().strftime('%H:%M:%S')}...")

        task_a = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "task-A"},
            task=True,
        )
        task_b = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "task-B"},
            task=True,
        )
        task_c = await client.call_tool(
            "long_running_task",
            {"duration": 1, "task_name": "task-C"},
            task=True,
        )

        print("[CLIENT] All tasks launched, waiting for completion...")

        # Gather results (they'll complete in different order based on duration)
        results = await asyncio.gather(task_a, task_b, task_c)

        elapsed = time.time() - start_time
        print(f"[CLIENT] All tasks completed in {elapsed:.2f}s (3+2+1=6s if serial, ~3s if concurrent)")

        for i, result in enumerate(results, 1):
            print(f"[CLIENT] Task {i} result: {result.data['message']}")

        # Example 3: Polling multiple task statuses concurrently
        print("\nExample 3: Poll multiple task statuses while they run")
        print("-" * 60)
        print("[CLIENT] Starting 3 tasks with different durations...")

        # Start 3 tasks
        poll_a = await client.call_tool(
            "long_running_task",
            {"duration": 5, "task_name": "poll-A"},
            task=True,
        )
        poll_b = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "poll-B"},
            task=True,
        )
        poll_c = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "poll-C"},
            task=True,
        )

        print("[CLIENT] All tasks launched, polling their statuses...\n")

        # Poll all tasks every 0.5 seconds and show their states
        tasks_map = {"poll-A (5s)": poll_a, "poll-B (3s)": poll_b, "poll-C (2s)": poll_c}
        completed_tasks = set()

        while len(completed_tasks) < len(tasks_map):
            states = []
            for name, task in tasks_map.items():
                if name not in completed_tasks:
                    status = await task.status()
                    state_str = f"{name}: {status.status}"
                    states.append(state_str)

                    if status.status in ["completed", "failed", "cancelled"]:
                        completed_tasks.add(name)
                        states[-1] += " ✓"
                else:
                    states.append(f"{name}: completed ✓")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] " + " | ".join(states))

            if len(completed_tasks) < len(tasks_map):
                await asyncio.sleep(0.5)

        print(f"\n[CLIENT] All tasks completed!\n")

        # Example 4: Compare with instant tool
        print("Example 4: Compare with non-task tool")
        print("-" * 60)
        instant_result = await client.call_tool(
            "instant_tool", {"message": "This returns immediately"}
        )
        print(f"[CLIENT] Instant tool result: {instant_result.data}\n")

        print("=" * 60)
        print("Demo completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
