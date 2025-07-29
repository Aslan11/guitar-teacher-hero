from __future__ import annotations

from typing import List

from pydantic import BaseModel
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent
    from openai_agents.workflows.guitar_tab_agents.instruction_agent import new_instruction_agent


class Clarifications(BaseModel):
    questions: List[str]


CLARIFYING_PROMPT = """Ask 2–3 short clarifying questions about the guitar request.
Always ask if the user prefers chords or tablature. Other helpful details
include skill level, which part of the song to focus on, and tuning or
style preferences."""


def new_clarifying_agent() -> Agent:
    instruction_agent = new_instruction_agent()
    return Agent(
        name="Guitar Clarifying Agent",
        model="gpt-4o-mini",
        instructions=CLARIFYING_PROMPT,
        output_type=Clarifications,
        handoffs=[instruction_agent],
    )
