# FastMCP Background Tasks Demo (SEP-1686)

This project demonstrates **task lifecycle management** in FastMCP using the experimental `sep-1686` branch. Learn how background tasks enable long-running operations that survive client disconnects, can be monitored from multiple clients, and persist beyond the initial connection.

**This demo shows:**
- ✅ **Concurrent execution** - Tasks run in parallel (3s+2s+1s = ~3s total)
- ✅ **Status polling** - Monitor task progress in real-time
- ✅ **Fire-and-forget patterns** - Submit work and check back later
- ✅ **Comparison with asyncio.gather** - Understand when to use each approach

## Understanding SEP-1686: Why Background Tasks Matter

### The Problem

Imagine you're building an MCP tool for molecular analysis in drug discovery. A single analysis takes **3 hours**. What happens if:
- Your laptop goes to sleep at hour 2?
- Your network connection drops?
- You need to check the status from your phone?
- Another team member needs to see if the analysis is done?

With traditional MCP tool calls, **the work is lost**. The client must stay connected for the entire duration, and only that client can access the result.

### What Background Tasks Actually Solve

**It's not about concurrency** - both `asyncio.gather` and `task=True` give you parallel execution (~3s in our demo).

**It's about task lifecycle management:**

#### 1. **Connection Independence**
```python
# Submit work and disconnect
task = await client.call_tool("analyze_molecules", {...}, task=True)
task_id = task.task_id  # Save this!

# Close laptop, go home, reconnect tomorrow
# Work continues on server

# Check back later from any device
status = await client.get_task_status(task_id)
result = await client.get_task_result(task_id)
```

#### 2. **Crash Resilience**
If your client crashes at hour 2 of a 3-hour analysis:
- **With normal calls**: Work is lost, start over (3 more hours)
- **With background tasks**: Work continues, just reconnect and retrieve result

#### 3. **Multiple Result Retrieval**
```python
# Get result on your laptop
result = await task.result()

# Later, get the same result on your phone
result = await client.get_task_result(task_id)  # Same result!

# Share task_id with teammate
# They can also retrieve the result
```

#### 4. **Multi-Client Coordination**
```python
# Team member A submits the analysis
task = await client.call_tool("run_tests", {...}, task=True)
# Shares task_id: "abc-123"

# Team member B (maybe in a dashboard)
status = await client.get_task_status("abc-123")
# "Still running... 45% complete"

# Team member C (mobile app)
if await client.get_task_status("abc-123").status == "completed":
    notify_slack("Tests passed!")
```

#### 5. **Server-Side Resource Management**
The server can:
- Queue tasks when resources are limited
- Prioritize important work
- Rate-limit per-user submissions
- Manage connection pools centrally

### Real-World Use Cases (from SEP-1686)

**Healthcare & Life Sciences**: Molecular property analysis processing 100,000+ data points through multiple models. Takes hours. Cannot re-run if connection drops.

**Enterprise Automation**: Code migrations across multiple repositories. Analyze dependencies, transform code, validate changes. Takes 20 minutes to 2 hours. Need to resume if laptop sleeps.

**Test Infrastructure**: Comprehensive test suites with thousands of cases. Takes hours. Need to stream logs while tests run, see which tests failed without waiting for entire suite.

**Deep Research**: Multi-agent research systems that spawn multiple research agents internally. Takes 10-30 minutes. Model can't "wait" in a single turn.

**CI/CD Pipelines**: Build, test, deploy workflows. Takes 15-45 minutes. Multiple team members need visibility into build status.

### When to Use What

**Use `asyncio.gather` when:**
- Operations complete quickly (&lt;30 seconds)
- Client will definitely stay connected
- Only one client needs the result
- Simple fan-out/fan-in pattern

```python
# Perfect for asyncio.gather
results = await asyncio.gather(
    client.call_tool("quick_lookup", {...}),
    client.call_tool("quick_search", {...}),
    client.call_tool("quick_parse", {...}),
)
```

**Use background tasks (`task=True`) when:**
- Operations take minutes or hours
- Client might disconnect (mobile, laptop sleep, network issues)
- Multiple clients need task visibility
- Need to retrieve results multiple times
- Building dashboards showing task progress
- Server needs to manage resources/rate limits

```python
# Perfect for background tasks
task = await client.call_tool("run_comprehensive_tests", {...}, task=True)

# Do other work, client can disconnect/reconnect
# Check back later from anywhere
result = await task.result()
```

### Key Insight

> **Both `asyncio.gather` and `task=True` give you concurrency** (~3s vs ~3s in our demo).
>
> **The difference is task lifecycle management.** Tasks persist beyond the connection, survive client crashes, can be queried by multiple clients, and results can be retrieved multiple times.
>
> Think of tasks like **submitting a job to a queue**, not just making concurrent API calls.

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
0. **Three Approaches Comparison** - Same 3 tools called different ways:
   - Sequential: 6.01s (one at a time)
   - `asyncio.gather`: 3.00s (client-side concurrency)
   - `task=True`: 3.05s (server-side background tasks)
   - **Key finding:** Both concurrent approaches are ~2x faster than sequential
   - **Unique value of tasks:** Status polling, fire-and-forget, observability
1. **What tasks enable** - Polling status while working (impossible with gather)
2. **Direct await** - Call task and immediately wait for result
3. **Concurrent tasks** - Launch multiple tasks simultaneously
4. **Status polling** - Monitor 3 tasks with real-time state transitions
5. **Instant tools** - Compare with non-task tools

### Client-Server Demo

Run the client connecting to the server:

```bash
uv run python client.py
```

This shows three usage patterns:
1. **Pattern 1: Direct Await** - Simplest approach
2. **Pattern 2: Status Polling** - Monitor progress
3. **Pattern 3: Manual Result Fetching** - Do work while task runs


**Real Version (Requires API Keys):**
```bash
# Install optional dependencies
uv sync --extra deep-research

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   ANTHROPIC_API_KEY=your-anthropic-key
#   GOOGLE_VERTEX_PROJECT=your-gcp-project

# Run with real AI agents (takes 10-30 minutes)
python deep_research_server.py
```

Uses real pydantic_ai agents:
- Claude Sonnet 4.5 for planning and analysis
- Gemini 2.5 Flash for web searches
- Demonstrates true long-running operations (minutes)

**Why This Matters:**
- Operations taking 10-30 minutes cannot use regular tool calls
- Client must be able to disconnect/reconnect
- Multiple team members need visibility into research status
- Results must persist beyond the original connection
- **This is impossible with `asyncio.gather`** - client must stay connected the entire time

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

## Three Ways to Call Multiple Tools

### Approach A: Sequential (6 seconds)

```python
# Each call waits for the previous to complete
result1 = await client.call_tool("my_tool", {"duration": 3}, task=False)
result2 = await client.call_tool("my_tool", {"duration": 2}, task=False)
result3 = await client.call_tool("my_tool", {"duration": 1}, task=False)
# Total: 3 + 2 + 1 = 6 seconds
```

### Approach B: asyncio.gather (3 seconds) ✨

```python
# Client-side concurrency - all calls run in parallel!
results = await asyncio.gather(
    client.call_tool("my_tool", {"duration": 3}, task=False),
    client.call_tool("my_tool", {"duration": 2}, task=False),
    client.call_tool("my_tool", {"duration": 1}, task=False),
)
# Total: max(3, 2, 1) = ~3 seconds
```

### Approach C: Background Tasks (3 seconds) ✨

```python
# Server-side background tasks - same speed, more features
task1 = await client.call_tool("my_tool", {"duration": 3}, task=True)
task2 = await client.call_tool("my_tool", {"duration": 2}, task=True)
task3 = await client.call_tool("my_tool", {"duration": 1}, task=True)

results = await asyncio.gather(task1, task2, task3)
# Total: max(3, 2, 1) = ~3 seconds
```

## Example Output

When running `demo.py`, you'll see output like:

```
COMPARISON: Serial (task=False) vs Concurrent (task=True)
======================================================================

Part A: Serial execution (task=False) - Traditional approach
----------------------------------------------------------------------
[CLIENT] Calling 3 tools serially (waiting for each to complete)...
  [SERVER] Task 'serial-A' starting, will run for 3s
  [SERVER] Task 'serial-A' completed after 3.00s
  [SERVER] Task 'serial-B' starting, will run for 2s
  [SERVER] Task 'serial-B' completed after 2.00s
  [SERVER] Task 'serial-C' starting, will run for 1s
  [SERVER] Task 'serial-C' completed after 1.00s
[CLIENT] ⏱️  Serial execution took: 6.01s
         (Expected: 3+2+1 = 6 seconds)

Part B: Concurrent execution (task=True) - Background tasks
----------------------------------------------------------------------
[CLIENT] Launching 3 tasks concurrently...
  [SERVER] Task 'concurrent-A' starting, will run for 3s
  [SERVER] Task 'concurrent-B' starting, will run for 2s
  [SERVER] Task 'concurrent-C' starting, will run for 1s
  [SERVER] Task 'concurrent-C' completed after 1.00s
  [SERVER] Task 'concurrent-B' completed after 2.00s
  [SERVER] Task 'concurrent-A' completed after 3.00s
[CLIENT] ⏱️  Concurrent execution took: 3.05s
         (Expected: max(3,2,1) = ~3 seconds)

🚀 Speedup: 1.97x faster with background tasks!
   Time saved: 2.96 seconds
```

## Learn More

- [FastMCP Repository](https://github.com/jlowin/fastmcp)
- [SEP-1686 Branch](https://github.com/jlowin/fastmcp/tree/sep-1686)
- [MCP Specification](https://modelcontextprotocol.io)

## License

This demo project follows the same license as FastMCP.
