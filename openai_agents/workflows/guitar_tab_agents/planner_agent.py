from __future__ import annotations

from pydantic import BaseModel

from agents import Agent

PLANNER_PROMPT = (
    "You help plan web searches to find guitar tablature and lessons. "
    "Given an instruction, list 3-6 search terms that will locate good tabs or relevant tutorials."
)


class WebSearchItem(BaseModel):
    reason: str
    query: str


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]


def new_planner_agent() -> Agent:
    return Agent(
        name="Guitar Planner Agent",
        instructions=PLANNER_PROMPT,
        model="gpt-4o",
        output_type=WebSearchPlan,
    )
