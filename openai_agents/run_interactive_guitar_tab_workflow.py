import argparse
import asyncio
from pathlib import Path
from typing import Dict, List

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from openai_agents.workflows.guitar_tab_workflow import InteractiveGuitarTabWorkflow
from openai_agents.workflows.research_agents.research_models import (
    ClarificationInput,
    SingleClarificationInput,
    UserQueryInput,
)


async def run_interactive_guitar_tab(client: Client, query: str, workflow_id: str):
    print(f"🎸 Starting interactive guitar tab session: {query}")

    handle = None
    start_new = True
    try:
        handle = client.get_workflow_handle(workflow_id)
        try:
            status = await handle.query(InteractiveGuitarTabWorkflow.get_status)
            if status and status.status not in ["completed", "failed", "timed_out", "terminated", "canceled"]:
                start_new = False
        except Exception:
            pass
    except Exception:
        pass

    if start_new:
        import time

        unique_id = f"{workflow_id}-{int(time.time())}"
        handle = await client.start_workflow(
            InteractiveGuitarTabWorkflow.run,
            args=[None, False],
            id=unique_id,
            task_queue="openai-agents-task-queue",
        )

    if not handle:
        raise RuntimeError("Failed to get workflow handle")

    status = await handle.query(InteractiveGuitarTabWorkflow.get_status)
    if not status or status.status == "pending":
        await handle.execute_update(InteractiveGuitarTabWorkflow.start_tab_session, UserQueryInput(query=query))

    while True:
        status = await handle.query(InteractiveGuitarTabWorkflow.get_status)
        if status.status in ["awaiting_clarifications", "collecting_answers"]:
            while status.get_current_question() is not None:
                current = status.get_current_question()
                print(current)
                answer = input("Your answer: ").strip()
                if answer.lower() in ["exit", "quit", "end", "done"]:
                    await handle.signal(InteractiveGuitarTabWorkflow.end_workflow_signal)
                    return
                status = await handle.execute_update(
                    InteractiveGuitarTabWorkflow.provide_single_clarification,
                    SingleClarificationInput(question_index=status.current_question_index, answer=answer or "No preference"),
                )
        elif status.status == "researching":
            print("Generating tablature... please wait")
            break
        elif status.status == "completed":
            break
        else:
            await asyncio.sleep(1)

    result = await handle.result()
    md_file = Path("guitar_tab.md")
    md_file.write_text(result.markdown_report)
    print(f"Markdown saved to: {md_file}")
    if result.pdf_file_path:
        print(f"PDF saved to: {result.pdf_file_path}")
    print(result.markdown_report)
    return result


async def main():
    parser = argparse.ArgumentParser(description="OpenAI Interactive Guitar Tab Workflow")
    parser.add_argument("query", nargs="?", help="Guitar request")
    parser.add_argument("--workflow-id", default="guitar-tab-workflow", help="Workflow ID")
    args = parser.parse_args()

    client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)

    query = args.query or input("Enter your guitar question: ").strip()
    await run_interactive_guitar_tab(client, query, args.workflow_id)


if __name__ == "__main__":
    asyncio.run(main())
