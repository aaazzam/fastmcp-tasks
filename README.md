# FastMCP Background Tasks Demo (SEP-1686)

This project demonstrates **true concurrent background task execution** in FastMCP using the experimental `sep-1686` branch. Watch multiple tasks run in parallel while you poll their status and retrieve results!

**This demo shows:**
- ✅ **Real concurrent execution** - 3 tasks (3s+2s+1s) complete in ~3s total
- ✅ Task-enabled server tools running in parallel
- ✅ Status polling while tasks run in the background
- ✅ Multiple usage patterns for task management

## What Are Background Tasks?

Background tasks in FastMCP (SEP-1686) enable **true concurrent tool execution**. When you call a tool with `task=True`, it returns immediately with a future-like object while the tool executes in the background.

### Features

- ✅ **Concurrent execution** - Multiple tasks run in parallel
- ✅ **Non-blocking API** - Call returns immediately with task handle
- ✅ **Status monitoring** - Poll task state while it runs
- ✅ **Flexible result retrieval** - Await when ready or poll periodically
- ✅ **In-memory task queue** - Uses Docket for background execution

**Critical requirement:** You must enable experimental settings:
```python
from fastmcp import settings
settings.experimental.enable_docket = True
settings.experimental.enable_tasks = True
```

Without these, tasks will execute synchronously.

## Project Structure

- `server.py` - FastMCP server with task-enabled tools
- `client.py` - Client demonstrating three different task usage patterns
- `demo.py` - Standalone demo combining server and client
- `pyproject.toml` - Project dependencies (fastmcp from sep-1686 branch)

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync
```

This will install fastmcp from the `sep-1686` branch on GitHub.

## Running the Demos

### Quick Demo (Recommended)

Run the standalone demo that shows all task patterns:

```bash
uv run python demo.py
```

This demonstrates:
1. **Direct await** - Call task and immediately wait for result
2. **Concurrent tasks** - Launch multiple tasks simultaneously
3. **Status polling** - Poll task status while it runs
4. **Instant tools** - Compare with non-task tools

### Client-Server Demo

Run the client connecting to the server:

```bash
uv run python client.py
```

This shows three usage patterns:
1. **Pattern 1: Direct Await** - Simplest approach
2. **Pattern 2: Status Polling** - Monitor progress
3. **Pattern 3: Manual Result Fetching** - Do work while task runs

## Server Implementation

### Step 1: Enable Experimental Settings

**Critical:** You must enable these settings before creating your server:

```python
from fastmcp import FastMCP, settings

# Enable experimental task support
settings.experimental.enable_docket = True
settings.experimental.enable_tasks = True

server = FastMCP(name="my-server")
```

### Step 2: Define Task-Enabled Tools

Tools are marked as task-enabled using `@server.tool(task=True)`:

```python
@server.tool(task=True)
async def long_running_task(duration: int) -> dict:
    """This tool can execute as a background task"""
    await asyncio.sleep(duration)  # Use async operations
    return {"status": "completed"}
```

## Client Usage

### Basic Pattern: Direct Await

```python
from fastmcp import Client

async with Client(server) as client:
    # Call tool with task=True
    task = await client.call_tool("my_tool", {...}, task=True)

    # Await the result
    result = await task
    print(result.data)
```

### Advanced Pattern: Status Polling

```python
# Create task
task = await client.call_tool("my_tool", {...}, task=True)

# Poll status
while True:
    status = await task.status()
    print(f"Status: {status.status}")

    if status.status in ["completed", "failed", "cancelled"]:
        break

    await asyncio.sleep(1)

# Get result
result = await task.result()
```

### Concurrent Tasks

```python
# Launch multiple tasks
task_a = await client.call_tool("tool_1", {...}, task=True)
task_b = await client.call_tool("tool_2", {...}, task=True)
task_c = await client.call_tool("tool_3", {...}, task=True)

# Wait for all to complete
results = await asyncio.gather(task_a, task_b, task_c)
```

## Important Notes

### Current Limitations (sep-1686 branch)

- **In-memory only** - Tasks run in a single process, not distributed across machines
- **FastMCP client only** - Can only invoke with the fastmcp client at this time
- **Experimental settings required** - Must explicitly enable `enable_docket` and `enable_tasks`
- **Experimental feature** - Under active development, API may change

Despite being in-memory/single-process, tasks **do execute concurrently** within that process using asyncio and the Docket task queue.

### API Details

**Task Object Methods:**
- `await task` - Wait for result (shorthand for `task.result()`)
- `await task.result()` - Get the final result
- `await task.status()` - Check current task status
- `await task.wait()` - Wait until task reaches terminal state
- `await task.cancel()` - Request task cancellation

**Result Access:**
Results are returned as `CallToolResult` objects. Access the actual data via `.data`:

```python
result = await task
print(result.data)  # The actual return value from your tool
```

**Status Values:**
- `submitted` - Task has been submitted
- `working` - Task is currently executing
- `completed` - Task finished successfully
- `failed` - Task encountered an error
- `cancelled` - Task was cancelled

## Example Output

When running `demo.py`, you'll see output like:

```
Example 1: Call task and await immediately
------------------------------------------------------------
  [SERVER] Task 'quick-task' starting, will run for 2s
  [SERVER] Task 'quick-task' completed after 2.01s
[CLIENT] Task object created: ToolTask
[CLIENT] Result: {'task_name': 'quick-task', 'message': "Task 'quick-task' finished successfully!"}

Example 2: Launch multiple tasks concurrently
------------------------------------------------------------
[CLIENT] Starting 3 tasks simultaneously...
  [SERVER] Task 'task-A' starting, will run for 3s
  [SERVER] Task 'task-A' completed after 3.01s
[CLIENT] Task 1 result: Task 'task-A' finished successfully!
```

## Learn More

- [FastMCP Repository](https://github.com/jlowin/fastmcp)
- [SEP-1686 Branch](https://github.com/jlowin/fastmcp/tree/sep-1686)
- [MCP Specification](https://modelcontextprotocol.io)

## License

This demo project follows the same license as FastMCP.
