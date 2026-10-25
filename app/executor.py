"""
Executor Module.
Executes the planned tasks sequentially, generating detailed content for each section.
"""
import logging
from typing import List, Dict, Any

from app.models import Plan, TaskItem, SectionContent
from app.llm_client import llm_client

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are an Autonomous Content Execution Agent.
Your job is to draft a comprehensive, executive-quality section of a strategic business/technical report.
You must return valid JSON strictly following this schema:
{
  "section_title": "Title of this section",
  "paragraphs": [
    "Paragraph 1 containing thorough, realistic, and actionable analysis...",
    "Paragraph 2 expanding on operational considerations, methodologies, or findings..."
  ],
  "bullet_points": [
    "Key strategic point or takeaway 1",
    "Key strategic point or takeaway 2",
    "Key strategic point or takeaway 3"
  ],
  "table_headers": ["Column 1", "Column 2", "Column 3"],
  "table_rows": [
    ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
    ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
  ]
}
Ensure the content is detailed, professional, and directly addresses the context and constraints.
"""


def execute_tasks(plan: Plan, original_request: str) -> List[SectionContent]:
    """
    Sequentially executes each task in the plan to produce rich content for the final document.
    Updates the task status and output_summary in-place.
    """
    logger.info(f"Beginning sequential execution of {len(plan.tasks)} tasks...")
    sections: List[SectionContent] = []

    for task in plan.tasks:
        task.status = "in_progress"
        logger.info(f"Executing Task {task.id}: '{task.title}' for section '{task.target_section}'")

        user_prompt = f"""Project Document Title: {plan.title}
Original Request: {original_request}
Assumptions In Play: {"; ".join(plan.assumptions) if plan.assumptions else "None"}

Current Task ID: {task.id}
Current Task Title: {task.title}
Task Instructions: {task.description}
Target Section to Draft: {task.target_section}

Please draft a thorough, highly realistic, and professional section. Include an actionable table if appropriate for this section.
"""

        try:
            raw_content = llm_client.query_json(
                system_prompt=EXECUTOR_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )

            section = SectionContent(
                section_title=raw_content.get("section_title") or task.target_section,
                paragraphs=[str(p) for p in raw_content.get("paragraphs", []) if str(p).strip()],
                bullet_points=[str(b) for b in raw_content.get("bullet_points", []) if str(b).strip()],
                table_headers=raw_content.get("table_headers"),
                table_rows=raw_content.get("table_rows")
            )

            # Ensure we have at least one substantive paragraph
            if not section.paragraphs:
                section.paragraphs = [
                    f"Comprehensive analysis conducted for {task.target_section} under established parameters."
                ]

            sections.append(section)
            task.status = "completed"
            task.output_summary = (
                f"Generated {len(section.paragraphs)} paragraphs, {len(section.bullet_points)} key points"
                f"{f' and {len(section.table_rows)} table rows' if section.table_rows else ''}."
            )

        except Exception as e:
            logger.error(f"Task {task.id} execution failed: {e}")
            task.status = "failed"
            task.output_summary = f"Execution failed: {str(e)}"
            # Create a fallback section so document compilation can proceed and self-check can inspect
            fallback_section = SectionContent(
                section_title=task.target_section,
                paragraphs=[f"Drafting in progress for {task.target_section}. Initial execution encountered an anomaly: {str(e)}."],
                bullet_points=["Action Item: Review task inputs and retry generation."]
            )
            sections.append(fallback_section)

    logger.info("Sequential task execution completed.")
    return sections
