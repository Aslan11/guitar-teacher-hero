from __future__ import annotations

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent
    from openai_agents.workflows.guitar_tab_agents.planner_agent import new_planner_agent


INSTRUCTION_PROMPT = """Combine the original guitar question with any clarification answers and produce a short paragraph describing exactly what tablature or lesson to generate."""


def new_instruction_agent() -> Agent:
    planner_agent = new_planner_agent()
    return Agent(
        name="Guitar Instruction Agent",
        model="gpt-4o-mini",
        instructions=INSTRUCTION_PROMPT,
        handoffs=[planner_agent],
    )
