from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from agents import (
        RunConfig,
        Runner,
        TResponseInputItem,
        custom_span,
        gen_trace_id,
        trace,
    )

    from openai_agents.workflows.guitar_tab_agents.clarifying_agent import Clarifications
    from openai_agents.workflows.research_agents.pdf_generator_agent import new_pdf_generator_agent
    from openai_agents.workflows.guitar_tab_agents.planner_agent import (
        WebSearchItem,
        WebSearchPlan,
        new_planner_agent,
    )
    from openai_agents.workflows.guitar_tab_agents.search_agent import new_search_agent
    from openai_agents.workflows.guitar_tab_agents.triage_agent import new_triage_agent
    from openai_agents.workflows.guitar_tab_agents.writer_agent import (
        ReportData,
        new_writer_agent,
    )


@dataclass
class ClarificationResult:
    needs_clarifications: bool
    questions: Optional[List[str]] = None
    research_output: Optional[str] = None
    report_data: Optional[ReportData] = None


class InteractiveGuitarTabManager:
    def __init__(self) -> None:
        self.run_config = RunConfig()
        self.search_agent = new_search_agent()
        self.planner_agent = new_planner_agent()
        self.writer_agent = new_writer_agent()
        self.triage_agent = new_triage_agent()
        self.pdf_generator_agent = new_pdf_generator_agent()

    async def _run_direct(self, query: str) -> ReportData:
        trace_id = gen_trace_id()
        with trace("Guitar tab trace", trace_id=trace_id):
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)
        return report

    async def run_with_clarifications_start(self, query: str) -> ClarificationResult:
        trace_id = gen_trace_id()
        with trace("Clarification check", trace_id=trace_id):
            input_items: list[TResponseInputItem] = [{"content": query, "role": "user"}]
            result = await Runner.run(
                self.triage_agent,
                input_items,
                run_config=self.run_config,
            )
            clarifications = self._extract_clarifications(result)
            if clarifications and isinstance(clarifications, Clarifications):
                return ClarificationResult(needs_clarifications=True, questions=clarifications.questions)
            else:
                search_plan = await self._plan_searches(query)
                search_results = await self._perform_searches(search_plan)
                report = await self._write_report(query, search_results)
                return ClarificationResult(
                    needs_clarifications=False,
                    research_output=report.markdown_report,
                    report_data=report,
                )

    async def run_with_clarifications_complete(self, original_query: str, questions: List[str], responses: Dict[str, str]) -> ReportData:
        trace_id = gen_trace_id()
        with trace("Enhanced Guitar Tab", trace_id=trace_id):
            enriched = self._enrich_query(original_query, questions, responses)
            search_plan = await self._plan_searches(enriched)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(enriched, search_results)
            return report

    def _extract_clarifications(self, result) -> Optional[Clarifications]:
        try:
            if hasattr(result, "final_output") and isinstance(result.final_output, Clarifications):
                return result.final_output
            for item in result.new_items:
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
                    content = item.raw_item.content
                    if isinstance(content, Clarifications):
                        return content
                if hasattr(item, "output") and isinstance(item.output, Clarifications):
                    return item.output
            try:
                clarifications = result.final_output_as(Clarifications)
                if clarifications:
                    return clarifications
            except Exception:
                pass
            return None
        except Exception:
            return None

    def _enrich_query(self, original_query: str, questions: List[str], responses: Dict[str, str]) -> str:
        enriched = f"Original query: {original_query}\n\nAdditional context:\n"
        for i, question in enumerate(questions):
            answer = responses.get(f"question_{i}", "No preference")
            enriched += f"- {question}: {answer}\n"
        return enriched

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(self.planner_agent, f"Query: {query}", run_config=self.run_config)
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        with custom_span("Search the web"):
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results = []
            for task in workflow.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
            return results

    async def _search(self, item: WebSearchItem) -> str | None:
        input_str = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(self.search_agent, input_str, run_config=self.run_config)
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        input_str = f"Original query: {query}\nSummarized search results: {search_results}"
        markdown_result = await Runner.run(self.writer_agent, input_str, run_config=self.run_config)
        return markdown_result.final_output_as(ReportData)

    async def _generate_pdf_report(self, report_data: ReportData) -> str | None:
        try:
            pdf_result = await Runner.run(
                self.pdf_generator_agent,
                f"Convert this markdown report to PDF:\n\n{report_data.markdown_report}",
                run_config=self.run_config,
            )
            pdf_output = pdf_result.final_output_as(type(pdf_result.final_output))
            if pdf_output.success:
                return pdf_output.pdf_file_path
        except Exception:
            pass
        return None
