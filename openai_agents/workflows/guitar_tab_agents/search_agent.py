from __future__ import annotations

from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings

SEARCH_PROMPT = (
    "Use web search to locate guitar tablature or relevant lesson material for the provided query. "
    "Summarize any useful tab lines or key points in a few short sentences."
)


def new_search_agent() -> Agent:
    return Agent(
        name="Guitar Search Agent",
        instructions=SEARCH_PROMPT,
        tools=[WebSearchTool()],
        model_settings=ModelSettings(tool_choice="required"),
    )
