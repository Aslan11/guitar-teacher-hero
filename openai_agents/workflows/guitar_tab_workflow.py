from dataclasses import dataclass
from typing import Any

from temporalio import workflow

from openai_agents.workflows.guitar_tab_manager import InteractiveGuitarTabManager
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    ResearchInteractionDict,
    SingleClarificationInput,
    UserQueryInput,
)


@dataclass
class InteractiveGuitarTabResult:
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]
    pdf_file_path: str | None = None


@workflow.defn
class InteractiveGuitarTabWorkflow:
    def __init__(self) -> None:
        self.manager = InteractiveGuitarTabManager()
        self.original_query: str | None = None
        self.clarification_questions: list[str] = []
        self.clarification_responses: dict[str, str] = {}
        self.current_question_index: int = 0
        self.report_data: Any | None = None
        self.completed: bool = False
        self.workflow_ended: bool = False
        self.initialized: bool = False

    def _build_result(
        self,
        summary: str,
        report: str,
        questions: list[str] | None = None,
        pdf_path: str | None = None,
    ) -> InteractiveGuitarTabResult:
        return InteractiveGuitarTabResult(
            short_summary=summary,
            markdown_report=report,
            follow_up_questions=questions or [],
            pdf_file_path=pdf_path,
        )

    @workflow.run
    async def run(self, initial_query: str | None = None, use_clarifications: bool = False) -> InteractiveGuitarTabResult:
        if initial_query and not use_clarifications:
            report = await self.manager._run_direct(initial_query)
            pdf = await self.manager._generate_pdf_report(report)
            return self._build_result(report.short_summary, report.markdown_report, report.follow_up_questions, pdf)

        while True:
            await workflow.wait_condition(
                lambda: self.workflow_ended or self.completed or self.initialized
            )

            if self.workflow_ended:
                return self._build_result("Session ended", "Workflow ended by user")

            if self.completed and self.report_data:
                pdf = await self.manager._generate_pdf_report(self.report_data)
                return self._build_result(
                    self.report_data.short_summary,
                    self.report_data.markdown_report,
                    self.report_data.follow_up_questions,
                    pdf,
                )

            if self.initialized and not self.completed:
                if self.clarification_questions:
                    await workflow.wait_condition(
                        lambda: self.workflow_ended or len(self.clarification_responses) >= len(self.clarification_questions)
                    )

                    if self.workflow_ended:
                        return self._build_result("Session ended", "Workflow ended by user")

                    if self.original_query:
                        self.report_data = await self.manager.run_with_clarifications_complete(
                            self.original_query,
                            self.clarification_questions,
                            self.clarification_responses,
                        )

                    self.completed = True
                    continue
                elif self.report_data is not None:
                    self.completed = True
                    continue
                return self._build_result("No result", "Workflow failed to start")

    def _get_current_question(self) -> str | None:
        if self.current_question_index >= len(self.clarification_questions):
            return None
        return self.clarification_questions[self.current_question_index]

    def _has_more_questions(self) -> bool:
        return self.current_question_index < len(self.clarification_questions)

    @workflow.query
    def get_status(self) -> ResearchInteractionDict:
        current_question = self._get_current_question()

        if self.workflow_ended:
            status = "ended"
        elif self.completed:
            status = "completed"
        elif self.clarification_questions and len(self.clarification_responses) < len(self.clarification_questions):
            status = "awaiting_clarifications" if len(self.clarification_responses) == 0 else "collecting_answers"
        elif self.original_query and not self.completed:
            status = "researching"
        else:
            status = "pending"

        return ResearchInteractionDict(
            original_query=self.original_query,
            clarification_questions=self.clarification_questions,
            clarification_responses=self.clarification_responses,
            current_question_index=self.current_question_index,
            current_question=current_question,
            status=status,
            research_completed=self.completed,
        )

    @workflow.update
    async def start_tab_session(self, input: UserQueryInput) -> ResearchInteractionDict:
        self.original_query = input.query
        result = await self.manager.run_with_clarifications_start(self.original_query)

        if result.needs_clarifications:
            self.clarification_questions = result.questions or []
        else:
            if result.report_data is not None:
                self.report_data = result.report_data
        self.initialized = True
        return self.get_status()

    @workflow.update
    async def provide_single_clarification(self, input: SingleClarificationInput) -> ResearchInteractionDict:
        question_key = f"question_{self.current_question_index}"
        self.clarification_responses[question_key] = input.answer
        self.current_question_index += 1
        return self.get_status()

    @workflow.update
    async def provide_clarifications(self, input: ClarificationInput) -> ResearchInteractionDict:
        self.clarification_responses = input.responses
        self.current_question_index = len(self.clarification_questions)
        return self.get_status()

    @workflow.signal
    async def end_workflow_signal(self) -> None:
        self.workflow_ended = True
