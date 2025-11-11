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

        # Example 0: COMPARISON - Serial vs Concurrent Execution
        print("=" * 70)
        print("COMPARISON: Serial (task=False) vs Concurrent (task=True)")
        print("=" * 70)

        # Part A: Serial execution (traditional way)
        print("\nPart A: Serial execution (task=False) - Traditional approach")
        print("-" * 70)
        serial_start = time.time()

        print("[CLIENT] Calling 3 tools serially (waiting for each to complete)...")
        result1 = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "serial-A"},
            task=False,  # NOT a task - blocks until complete
        )
        result2 = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "serial-B"},
            task=False,
        )
        result3 = await client.call_tool(
            "long_running_task",
            {"duration": 1, "task_name": "serial-C"},
            task=False,
        )

        serial_elapsed = time.time() - serial_start
        print(f"[CLIENT] ⏱️  Serial execution took: {serial_elapsed:.2f}s")
        print(f"         (Expected: 3+2+1 = 6 seconds)\n")

        # Part B: Concurrent execution (with tasks)
        print("Part B: Concurrent execution (task=True) - Background tasks")
        print("-" * 70)
        concurrent_start = time.time()

        print("[CLIENT] Launching 3 tasks concurrently...")
        task1 = await client.call_tool(
            "long_running_task",
            {"duration": 3, "task_name": "concurrent-A"},
            task=True,  # Returns immediately
        )
        task2 = await client.call_tool(
            "long_running_task",
            {"duration": 2, "task_name": "concurrent-B"},
            task=True,
        )
        task3 = await client.call_tool(
            "long_running_task",
            {"duration": 1, "task_name": "concurrent-C"},
            task=True,
        )

        print("[CLIENT] All tasks launched! Waiting for completion...")
        results = await asyncio.gather(task1, task2, task3)

        concurrent_elapsed = time.time() - concurrent_start
        print(f"[CLIENT] ⏱️  Concurrent execution took: {concurrent_elapsed:.2f}s")
        print(f"         (Expected: max(3,2,1) = ~3 seconds)")

        # Show the speedup
        speedup = serial_elapsed / concurrent_elapsed
        print(f"\n🚀 Speedup: {speedup:.2f}x faster with background tasks!")
        print(f"   Time saved: {serial_elapsed - concurrent_elapsed:.2f} seconds\n")

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
