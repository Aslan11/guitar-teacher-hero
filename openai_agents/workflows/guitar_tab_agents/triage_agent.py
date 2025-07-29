from __future__ import annotations

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import Agent
    from openai_agents.workflows.guitar_tab_agents.clarifying_agent import new_clarifying_agent
    from openai_agents.workflows.guitar_tab_agents.instruction_agent import new_instruction_agent


TRIAGE_AGENT_PROMPT = """You are a triage agent that decides if a guitar request needs clarifying questions.

Route to **CLARIFYING AGENT** when the request omits musical details such as whether the user wants chords or tablature, their skill level, or which section of a song to focus on. Also ask for clarifications for very broad requests like "teach me guitar".

Route to **INSTRUCTION AGENT** only when the request already specifies all the key details (e.g. the exact song section, that tabs are preferred, and the player's skill level).

Return exactly ONE function-call."""


def new_triage_agent() -> Agent:
    clarifying_agent = new_clarifying_agent()
    instruction_agent = new_instruction_agent()

    return Agent(
        name="Guitar Triage Agent",
        model="gpt-4o-mini",
        instructions=TRIAGE_AGENT_PROMPT,
        handoffs=[clarifying_agent, instruction_agent],
    )
