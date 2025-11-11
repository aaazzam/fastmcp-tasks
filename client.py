"""
FastMCP Client demonstrating background task usage patterns (SEP-1686)

This client shows three different ways to interact with background tasks:
1. Direct await - Call and immediately wait for result
2. Status polling - Call, poll status, then get result
3. Manual result fetching - Call, do other work, fetch result later
"""

import asyncio
from datetime import datetime

from fastmcp import Client

from server import mcp


async def pattern_1_direct_await(client: Client):
    """
    Pattern 1: Direct await
    Call the tool as a task and immediately await the result.
    """
    print("\n=== Pattern 1: Direct Await ===")
    print(f"[{datetime.now().isoformat()}] Calling slow_calculation(5) as task...")

    # Call tool with task=True and immediately await
    task = await client.call_tool("slow_calculation", {"n": 5}, task=True)
    print(f"Task created: {task}")

    # Directly await the task (equivalent to await task.result())
    result = await task
    print(f"[{datetime.now().isoformat()}] Result: {result.data}")


async def pattern_2_status_polling(client: Client):
    """
    Pattern 2: Status polling
    Call the tool as a task, poll its status, then get the result.
    """
    print("\n=== Pattern 2: Status Polling ===")
    print(f"[{datetime.now().isoformat()}] Calling fetch_data('api-server', 4) as task...")

    # Call tool with task=True
    task = await client.call_tool(
        "fetch_data", {"source": "api-server", "delay": 4}, task=True
    )
    print(f"Task created: {task}")

    # Poll status periodically
    print("Polling task status...")
    while True:
        status = await task.status()
        print(f"  Status: {status.status} ({datetime.now().isoformat()})")

        # Check if task reached a terminal state
        if status.status in ["completed", "failed", "cancelled"]:
            break

        # Wait a bit before polling again
        await asyncio.sleep(1)

    # Get the result
    result = await task.result()
    print(f"[{datetime.now().isoformat()}] Result: {result.data}")


async def pattern_3_manual_result_fetching(client: Client):
    """
    Pattern 3: Manual result fetching
    Call the tool as a task, do other work, then fetch result later.
    """
    print("\n=== Pattern 3: Manual Result Fetching ===")
    print(
        f"[{datetime.now().isoformat()}] Calling process_batch with 5 items as task..."
    )

    # Call tool with task=True
    task = await client.call_tool(
        "process_batch",
        {"items": ["apple", "banana", "cherry", "date", "elderberry"], "process_time_per_item": 0.5},
        task=True,
    )
    print(f"Task created: {task}")

    # Do other work while task runs in background
    print("Doing other work while task runs...")
    for i in range(3):
        await asyncio.sleep(1)
        print(f"  Other work step {i + 1}/3...")

    # Check status
    status = await task.status()
    print(f"Task status after other work: {status.status}")

    # Wait for completion and get result
    print("Waiting for task to complete...")
    await task.wait()  # Wait until task reaches a terminal state

    result = await task.result()
    print(f"[{datetime.now().isoformat()}] Result: {result.data}")


async def demonstrate_regular_tool(client: Client):
    """
    For comparison: calling a regular (non-task) tool
    """
    print("\n=== Regular Tool (non-task) ===")
    result = await client.call_tool("quick_task", {"message": "Hello from client!"})
    print(f"Result: {result}")


async def main():
    """
    Main function that connects to the server and demonstrates all patterns
    """
    print("FastMCP Task Demo Client")
    print("=" * 50)

    # Create client connected to our in-memory server
    client = Client(mcp)

    async with client:
        print(f"Connected to server: {mcp.name}")

        # List available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools: {[tool.name for tool in tools]}")

        # Demonstrate all patterns
        await pattern_1_direct_await(client)
        await pattern_2_status_polling(client)
        await pattern_3_manual_result_fetching(client)
        await demonstrate_regular_tool(client)

        print("\n" + "=" * 50)
        print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
