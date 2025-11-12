"""
Helper to add logging to FastMCP task polling.

This monkey-patches the Client.wait_for_task method to add detailed polling logs.
"""

import logging
import time
from typing import Any

logger = logging.getLogger("task-polling")


def enable_task_polling_logs(client: Any) -> None:
    """
    Add logging to a FastMCP client's task polling.

    Wraps the wait_for_task method to show:
    - When polling starts
    - Each status check (with throttling to avoid spam)
    - State transitions
    - When task completes

    Args:
        client: FastMCP Client instance
    """
    original_wait_for_task = client.wait_for_task

    async def logged_wait_for_task(
        task_id: str,
        *,
        state: str | None = None,
        timeout: float = 300.0,
        poll_interval: float = 0.05,
    ):
        """Wrapped version of wait_for_task with logging."""
        logger.info(f"⏳ Polling task {task_id[:8]}... (target: {state or 'completion'})")

        start = time.time()
        last_status = None
        poll_count = 0
        last_log_time = 0
        log_throttle = 2.0  # Log every 2 seconds max

        # Call original but intercept to add logging
        terminal_states = {"completed", "failed"}

        while time.time() - start < timeout:
            status = await client.get_task_status(task_id)
            current_state = status.status
            poll_count += 1
            elapsed = time.time() - start

            # Log state transitions
            if current_state != last_status:
                logger.info(f"  Task {task_id[:8]}: {last_status or 'unknown'} → {current_state}")
                last_status = current_state
                last_log_time = elapsed
            # Throttled progress logs
            elif elapsed - last_log_time >= log_throttle:
                logger.info(f"  Task {task_id[:8]}: still {current_state} ({poll_count} polls, {elapsed:.1f}s)")
                last_log_time = elapsed

            # Check if we've reached the desired state
            if state is not None:
                if current_state == state:
                    logger.info(f"✓ Task {task_id[:8]} reached '{state}' after {elapsed:.1f}s ({poll_count} polls)")
                    return status
            else:
                # No specific state requested - wait for terminal state
                if current_state in terminal_states:
                    logger.info(f"✓ Task {task_id[:8]} {current_state} after {elapsed:.1f}s ({poll_count} polls)")
                    return status

            import asyncio
            await asyncio.sleep(poll_interval)

        # Timeout
        logger.error(f"✗ Task {task_id[:8]} timeout after {timeout}s ({poll_count} polls)")
        if state is not None:
            raise TimeoutError(
                f"Task {task_id} did not reach state '{state}' within {timeout}s"
            )
        else:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    # Replace the method
    client.wait_for_task = logged_wait_for_task
    logger.info("Task polling logging enabled")
