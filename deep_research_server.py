"""
Deep Research Server with Real AI Agents

This implements the pydantic_ai deep research example as a FastMCP background task.

SETUP:
1. Copy .env.example to .env
2. Add your API keys to .env:
   - ANTHROPIC_API_KEY (for Claude Sonnet)
   - GOOGLE_VERTEX_PROJECT (for Gemini via Vertex AI)
3. Configure Google Cloud credentials

If you don't have API keys, use deep_research_mock_server.py instead.

Based on: https://ai.pydantic.dev/examples/deep-research/
"""

import asyncio
import os
import warnings
from typing import Annotated, Optional

from annotated_types import MaxLen
from dotenv import load_dotenv
from fastmcp import FastMCP, settings as fastmcp_settings
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, RunContext, WebSearchTool, format_as_xml
from pydantic_ai.agent import AbstractAgent
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file FIRST
load_dotenv()

# Suppress pydantic_ai deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic_ai")


# ============================================================================
# Configuration with pydantic-settings
# ============================================================================


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required for deep research
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key for Claude Sonnet",
    )
    gemini_api_key: str = Field(
        ...,
        description="Direct Gemini API key",
    )

    # Optional (if using Vertex AI instead)
    google_vertex_project: Optional[str] = Field(
        None,
        description="Google Cloud project ID for Vertex AI (not needed if using direct Gemini API)",
    )


# Load settings from .env
try:
    settings = Settings()
except Exception as e:
    print("\n❌ ERROR: Failed to load settings from .env file")
    print(f"   {e}")
    print("\n📝 Setup instructions:")
    print("   1. Copy .env.example to .env")
    print("   2. Add your API keys to .env")
    print("   3. Run: uv sync --extra deep-research")
    print("\n   Or use: deep_research_mock_server.py (no API keys required)\n")
    exit(1)

# Enable experimental task support
fastmcp_settings.experimental.enable_docket = True
fastmcp_settings.experimental.enable_tasks = True

# Create the FastMCP server
mcp = FastMCP(
    name="deep-research-server",
    instructions="Deep research server using AI agents for comprehensive analysis",
)


# ============================================================================
# Pydantic AI Agents (from original example)
# ============================================================================


class WebSearchStep(BaseModel):
    """A step that performs a web search."""

    search_terms: str


class DeepResearchPlan(BaseModel, **ConfigDict(use_attribute_docstrings=True)):
    """A structured plan for deep research."""

    executive_summary: str
    """A summary of the research plan."""

    web_search_steps: Annotated[list[WebSearchStep], MaxLen(5)]
    """A list of web search steps to perform to gather raw information."""

    analysis_instructions: str
    """The analysis step to perform after all web search steps are completed."""


# Planning agent - creates research plan
plan_agent = Agent(
    "anthropic:claude-sonnet-4-5",
    instructions="Analyze the users query and design a plan for deep research to answer their query.",
    output_type=DeepResearchPlan,
    name="abstract_plan_agent",
)

# Search agent - performs web searches
search_agent = Agent(
    "google-gla:gemini-2.5-flash",
    instructions="Perform a web search for the given terms and return a detailed report on the results.",
    builtin_tools=[WebSearchTool()],
    name="search_agent",
)

# Analysis agent - synthesizes findings
analysis_agent = Agent(
    "anthropic:claude-sonnet-4-5",
    deps_type=AbstractAgent,
    instructions="""
Analyze the research from the previous steps and generate a report on the given subject.

If the search results do not contain enough information, you may perform further searches using the
`extra_search` tool.
""",
    name="analysis_agent",
)


@analysis_agent.tool
async def extra_search(ctx: RunContext[AbstractAgent], query: str) -> str:
    """Perform an extra search for the given query."""
    result = await ctx.deps.run(query)
    return result.output


@mcp.tool(task=True)
async def web_search(search_terms: str) -> str:
    """
    Perform a single web search using AI agent.

    This is a background task - can take 10-60 seconds depending on search complexity.

    Args:
        search_terms: The search terms to look for

    Returns:
        str: Detailed report on search results
    """
    result = await search_agent.run(search_terms)
    return result.output


# ============================================================================
# FastMCP Tools - Composable Research Pipeline
# ============================================================================
#
# This demonstrates task composition: exposing each step as a separate tool
# so clients can orchestrate complex multi-agent workflows using MCP tasks.


@mcp.tool()
async def plan_research(query: str) -> dict:
    """
    Create a research plan for a query using Claude Sonnet.

    Analyzes the query and designs search steps. Fast operation (~5-10 seconds).

    Args:
        query: The research question

    Returns:
        dict: Research plan with search_steps list and analysis_instructions
    """
    result = await plan_agent.run(query)
    plan = result.output

    return {
        "executive_summary": plan.executive_summary,
        "search_steps": [step.search_terms for step in plan.web_search_steps],
        "analysis_instructions": plan.analysis_instructions,
    }


@mcp.tool(task=True)
async def analyze_research(query: str, search_results: list[str], instructions: str) -> str:
    """
    Analyze research results and generate final report using Claude Sonnet.

    This is a background task that can take 1-5 minutes.

    Args:
        query: Original research query
        search_results: Results from all searches
        instructions: Analysis instructions from plan

    Returns:
        str: Final research report
    """
    analysis_result = await analysis_agent.run(
        format_as_xml(
            {
                "query": query,
                "search_results": search_results,
                "instructions": instructions,
            }
        ),
        deps=search_agent,
    )

    return analysis_result.output


if __name__ == "__main__":
    # Settings already validated when loaded from .env above
    mcp.run(transport="stdio")
