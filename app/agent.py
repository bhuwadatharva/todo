"""
Agent Orchestrator Module.
Manages the end-to-end autonomous agent workflow:
Request -> Validation -> LLM Planning -> Plan Validation -> Sequential Task Execution
-> DOCX Generation -> Self-Check / Reflection -> JSON Response.
"""
import time
import logging
from pathlib import Path
from typing import Dict, Any

from app.models import AgentRequest, AgentResponse, Plan
from app.planner import generate_plan, validate_plan
from app.executor import execute_tasks
from app.document import create_docx_report
from app.reflection import perform_self_check_and_repair
from app.llm_client import llm_client

logger = logging.getLogger(__name__)


def run_agent(request_text: str) -> AgentResponse:
    """
    Executes the full autonomous pipeline.
    """
    start_time = time.time()
    logger.info(f"Received agent request: {request_text[:100]}...")

    try:
        # 1. LLM Planning Phase
        plan: Plan = generate_plan(request_text)

        # 2. Plan Validation Phase
        validate_plan(plan)

        # 3. Sequential Task Execution Phase
        sections = execute_tasks(plan, request_text)

        # 4. Polished DOCX Generation Phase
        initial_file_path = create_docx_report(plan, sections, request_text)

        # 5. Reflection / Self-Check Phase (with 1 repair attempt if needed)
        self_check = perform_self_check_and_repair(
            file_path=initial_file_path,
            plan=plan,
            sections=sections,
            request_text=request_text
        )

        elapsed = round(time.time() - start_time, 2)
        status = "success" if self_check.passed else "failed"
        filename = initial_file_path.name
        rel_path = f"output/{filename}"

        return AgentResponse(
            status=status,
            request=request_text,
            document_title=plan.title,
            assumptions=plan.assumptions,
            tasks=plan.tasks,
            document_path=rel_path,
            download_url=f"/download/{filename}",
            self_check=self_check,
            execution_time_seconds=elapsed,
            llm_provider=llm_client.get_provider_name(),
            error=None if self_check.passed else self_check.details
        )

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logger.error(f"Agent pipeline failed: {e}", exc_info=True)
        return AgentResponse(
            status="failed",
            request=request_text,
            document_title="Execution Failure",
            assumptions=[],
            tasks=[],
            document_path="",
            download_url="",
            self_check={
                "passed": False,
                "file_exists": False,
                "file_size_bytes": 0,
                "sections_found": [],
                "missing_sections": [],
                "repair_attempted": False,
                "details": f"Fatal pipeline error: {str(e)}"
            },
            execution_time_seconds=elapsed,
            llm_provider=llm_client.get_provider_name(),
            error=str(e)
        )
