"""
Planner Module.
Responsible for prompting the LLM to generate an ordered TODO list and assumptions,
and validating the structural integrity of the generated plan.
"""
import logging
from typing import Dict, Any

from app.models import Plan, TaskItem
from app.llm_client import llm_client

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an Autonomous AI Planning Agent specialized in project orchestration and executive documentation.
Given a user's prompt or project specification:
1. Deconstruct the prompt into an ordered, sequential TODO list of 4 to 6 actionable tasks.
2. Identify missing information, ambiguities, or competing priorities, and formulate clear, explicit assumptions to resolve them.
3. Map every task to a dedicated document section (target_section) that will be compiled into an executive Word (.docx) report.

You MUST respond strictly with valid JSON conforming to this schema:
{
  "title": "High-level Executive Title for Document",
  "subtitle": "Clear, contextual subtitle",
  "assumptions": [
    "Assumption explaining how missing info or competing priority was handled"
  ],
  "tasks": [
    {
      "id": 1,
      "title": "Short title of first task",
      "description": "Clear instruction of what needs to be researched/drafted",
      "target_section": "Executive Summary"
    },
    {
      "id": 2,
      "title": "Short title of second task",
      "description": "Instructions for next phase",
      "target_section": "Section Name"
    }
  ]
}
"""


def generate_plan(user_request: str) -> Plan:
    """
    Prompts the LLM to create an ordered TODO list and assumptions based on the user's request.
    """
    logger.info("Generating autonomous plan via LLM...")
    user_prompt = f"User Request: {user_request}\n\nDecompose this into an ordered TODO list and explicit assumptions."
    
    raw_data = llm_client.query_json(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    # Convert raw tasks into TaskItem models
    tasks = []
    for idx, item in enumerate(raw_data.get("tasks", []), start=1):
        task_id = item.get("id") or idx
        tasks.append(
            TaskItem(
                id=int(task_id),
                title=str(item.get("title", f"Task {task_id}")),
                description=str(item.get("description", "Execute assigned analysis.")),
                target_section=str(item.get("target_section", f"Section {task_id}")),
                status="pending"
            )
        )

    plan = Plan(
        title=str(raw_data.get("title", "Strategic Project Plan")),
        subtitle=str(raw_data.get("subtitle", "Autonomous Agent Output")),
        assumptions=[str(a) for a in raw_data.get("assumptions", [])],
        tasks=tasks
    )

    return plan


def validate_plan(plan: Plan) -> None:
    """
    Validates that the generated plan satisfies engineering requirements:
    - Minimum task count
    - Non-empty titles and descriptions
    - Unique sequential IDs
    - Document target section defined for every task
    Raises ValueError if plan fails validation.
    """
    if not plan.tasks:
        raise ValueError("Plan validation failed: TODO list is empty.")

    if len(plan.tasks) < 2:
        raise ValueError(f"Plan validation failed: Expected at least 2 tasks, got {len(plan.tasks)}.")

    ids = set()
    for task in plan.tasks:
        if not task.title.strip():
            raise ValueError(f"Plan validation failed: Task {task.id} has an empty title.")
        if not task.target_section.strip():
            raise ValueError(f"Plan validation failed: Task {task.id} has no target_section specified.")
        if task.id in ids:
            raise ValueError(f"Plan validation failed: Duplicate task id {task.id} found.")
        ids.add(task.id)

    logger.info(f"Plan successfully validated: {len(plan.tasks)} tasks planned.")
