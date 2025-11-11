"""
Standalone demo of FastMCP background tasks (SEP-1686)

This script creates both a server and client in one file,
demonstrating the complete task lifecycle.
"""

import asyncio
import time
from datetime import datetime

from fastmcp import Client, FastMCP

# Create the server
server = FastMCP(name="demo-server")


@server.tool(task=True)
def long_running_task(duration: int, task_name: str) -> dict:
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

    time.sleep(duration)

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
        print("[CLIENT] Starting 3 tasks simultaneously...")

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

        for i, result in enumerate(results, 1):
            print(f"[CLIENT] Task {i} result: {result.data['message']}")

        # Example 3: Polling task status
        print("\nExample 3: Poll task status while it runs")
        print("-" * 60)
        task_poll = await client.call_tool(
            "long_running_task",
            {"duration": 4, "task_name": "polled-task"},
            task=True,
        )
        print("[CLIENT] Task created, polling status...")

        # Poll every second
        for _ in range(5):
            status = await task_poll.status()
            print(f"[CLIENT]   Status: {status.status} at {datetime.now().strftime('%H:%M:%S')}")
            if status.status in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(1)

        result_poll = await task_poll.result()
        print(f"[CLIENT] Final result: {result_poll.data['message']}\n")

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
