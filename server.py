"""
FastMCP Server with Background Task Support (SEP-1686)

This server demonstrates task-enabled tools that can execute in the background.
"""

import asyncio
import time
from datetime import datetime

from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP(
    name="task-demo-server",
    instructions="A demo server showcasing background task execution with SEP-1686",
)


@mcp.tool(task=True)
def slow_calculation(n: int) -> dict:
    """
    Simulates a long-running calculation by sleeping for n seconds.

    Args:
        n: Number of seconds to sleep (simulating computation time)

    Returns:
        A dictionary with the result and timing information
    """
    start_time = time.time()
    time.sleep(n)
    end_time = time.time()

    return {
        "result": n * n,
        "computation_time": round(end_time - start_time, 2),
        "completed_at": datetime.now().isoformat(),
    }


@mcp.tool(task=True)
async def fetch_data(source: str, delay: int = 3) -> dict:
    """
    Simulates fetching data from a remote source with async delay.

    Args:
        source: The name of the data source to fetch from
        delay: Seconds to wait before returning data

    Returns:
        Simulated data from the source
    """
    await asyncio.sleep(delay)

    return {
        "source": source,
        "data": [f"item_{i}" for i in range(10)],
        "fetched_at": datetime.now().isoformat(),
        "delay_seconds": delay,
    }


@mcp.tool(task=True)
def process_batch(items: list[str], process_time_per_item: float = 0.5) -> dict:
    """
    Simulates batch processing of items.

    Args:
        items: List of items to process
        process_time_per_item: Time in seconds to process each item

    Returns:
        Processing results and statistics
    """
    start_time = time.time()
    processed = []

    for item in items:
        time.sleep(process_time_per_item)
        processed.append(f"processed_{item}")

    end_time = time.time()

    return {
        "processed_items": processed,
        "total_items": len(items),
        "total_time": round(end_time - start_time, 2),
        "completed_at": datetime.now().isoformat(),
    }


@mcp.tool()
def quick_task(message: str) -> str:
    """
    A regular synchronous tool that executes immediately (not task-enabled).

    Args:
        message: A message to echo back

    Returns:
        The echoed message with a timestamp
    """
    return f"Echo at {datetime.now().isoformat()}: {message}"


if __name__ == "__main__":
    # Run the server with stdio transport
    mcp.run(transport="stdio")
