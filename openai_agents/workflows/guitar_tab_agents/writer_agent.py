from __future__ import annotations

from pydantic import BaseModel
from agents import Agent

PROMPT = (
    "You are a guitar instructor creating ASCII tablature in markdown. "
    "Given the user's request and summarized search results, output a short introduction followed by the tablature wrapped in a fenced code block."
)


class ReportData(BaseModel):
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str] = []


def new_writer_agent() -> Agent:
    return Agent(
        name="Guitar Writer Agent",
        instructions=PROMPT,
        model="o3-mini",
        output_type=ReportData,
    )
